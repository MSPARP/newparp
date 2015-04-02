from flask import Flask, abort, current_app, g, jsonify, redirect, render_template, request, url_for
from functools import wraps
from math import ceil
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased, joinedload, joinedload_all
from sqlalchemy.orm.exc import NoResultFound
from webhelpers import paginate

from charat2.helpers import alt_formats
from charat2.helpers.auth import log_in_required
from charat2.helpers.chat import UnauthorizedException, BannedException, authorize_joining, send_message
from charat2.model import (
    case_options,
    AnyChat,
    Ban,
    Character,
    Chat,
    ChatUser,
    GroupChat,
    Message,
    PMChat,
    SearchCharacterGroup,
    User,
)
from charat2.model.connections import use_db
from charat2.model.validators import url_validator


def get_chat(f):
    @wraps(f)
    def decorated_function(url, fmt=None, *args, **kwargs):

        # Helper for doing some special URL stuff with PM chats.
        # Normally we just query for a Chat object with the url. However, PM chat
        # URLs take the form "pm/<username>", so we have to look up the username,
        # find the User it belongs to, and use our URL and theirs to create a
        # special URL.

        if url == "pm":
            abort(404)

        elif url.startswith("pm/"):

            username = url[3:]
            if username == "":
                abort(404)

            # You can't PM yourself.
            if username.lower() == g.user.username.lower():
                abort(404)

            try:
                pm_user = g.db.query(User).filter(
                    func.lower(User.username) == username.lower()
                ).one()
            except NoResultFound:
                abort(404)

            # Fix case if necessary.
            if pm_user.username != username:
                if request.method != "GET":
                    abort(404)
                return redirect(url_for(request.endpoint, url="pm/" + pm_user.username, fmt=fmt))

            # Generate URL from our user ID and their user ID.
            # Sort so they're always in the same order.
            pm_url = "pm/" + ("/".join(sorted([str(g.user.id), str(pm_user.id)])))
            try:
                chat = g.db.query(PMChat).filter(
                    PMChat.url == pm_url,
                ).one()
            except NoResultFound:
                # Only create a new PMChat on the main chat page.
                if request.endpoint != "rp_chat":
                    abort(404)
                chat = PMChat(url=pm_url)
                g.db.add(chat)
                g.db.flush()
                # Create ChatUser for the other user.
                pm_chat_user = ChatUser.from_user(pm_user, chat_id=chat.id, number=1)
                g.db.add(pm_chat_user)
                g.db.flush()

            return f(chat, pm_user, url, fmt, *args, **kwargs)

        # Force lower case.
        if url != url.lower():
            if request.method != "GET":
                abort(404)
            return redirect(url_for(request.endpoint, url=url.lower(), fmt=fmt))

        try:
            chat = g.db.query(AnyChat).filter(AnyChat.url == url).one()
        except NoResultFound:
            abort(404)

        g.chat = chat
        g.chat_id = chat.id
        try:
            authorize_joining(g.redis, g.db, g)
        except BannedException:
            if request.endpoint != "rp_chat" or chat.url == "theoubliette":
                abort(403)
            if request.method != "GET":
                abort(404)
            return redirect(url_for(request.endpoint, url="theoubliette", fmt=fmt))

        return f(chat, None, url, fmt, *args, **kwargs)

    return decorated_function


@use_db
@log_in_required
def create_chat():

    # Silently truncate to 50 because we've got a maxlength on the <input>.
    url = request.form["url"][:50]

    # Change URL to lower case but remember the original case for the title.
    lower_url = url.lower()

    if url_validator.match(lower_url) is None:
        return redirect(url_for("rp_groups", create_chat_error="url_invalid"))

    title = url.replace("_", " ").strip()
    # Don't allow titles to consist entirely of spaces. #idlersmells
    if len(title) == 0:
        title = lower_url

    # Check the URL against the routing to make sure it doesn't crash into any
    # of the other routes.
    route, args = current_app.url_map.bind("").match("/" + lower_url)
    if route != "rp_chat":
        return redirect(url_for("rp_groups", create_chat_error="url_taken"))

    # Don't allow pm because subchats of it (pm/*) will crash into private
    # chat URLs.
    if url == "pm" or g.db.query(Chat.id).filter(Chat.url == lower_url).count() != 0:
        return redirect(url_for("rp_groups", create_chat_error="url_taken"))

    g.db.add(GroupChat(
        url=lower_url,
        title=title,
        creator_id=g.user.id,
    ))
    return redirect(url_for("rp_chat", url=lower_url))


# XXX CUSTOM LOG IN/REGISTER PAGE WITH CHAT INFO
@alt_formats(set(["json"]))
@use_db
@log_in_required
@get_chat
def chat(chat, pm_user, url, fmt=None):

    chat_dict = chat.to_dict()

    if chat.type == "pm":
        # Override title with the other person's username.
        chat_dict['title'] = "Messaging " + pm_user.username
        chat_dict['url'] = url

    # Get or create ChatUser.
    try:
        chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.user_id == g.user.id,
            ChatUser.chat_id == chat.id,
        )).one()
    except NoResultFound:
        # Don't allow more than 2 people in roulette chats.
        if chat.type == "roulette":
            return redirect(url_for("rp_log", url=url))
        new_number = (g.db.query(func.max(ChatUser.number)).filter(ChatUser.chat_id == chat.id).scalar() or 0) + 1
        chat_user = ChatUser.from_user(g.user, chat_id=chat.id, number=new_number)
        if chat.type == "group" and g.user.id != chat.creator_id:
            chat_user.subscribed = False
        if (
            chat.type == "group" and chat.autosilence
            and g.user.group != "admin" and g.user.id != chat.creator_id
        ):
            chat_user.group = "silent"
        g.db.add(chat_user)
        g.db.flush()

    # Show the last 50 messages.
    messages = g.db.query(Message).filter(
        Message.chat_id == chat.id,
    ).options(joinedload(Message.chat_user)).order_by(
        Message.posted.desc(),
    ).limit(50).all()
    messages.reverse()

    latest_num = messages[-1].id if len(messages) > 0 else 0

    if fmt == "json":

        return jsonify({
            "chat": chat_dict,
            "chat_user": chat_user.to_dict(include_options=True),
            "messages": [
                _.to_dict() for _ in messages
            ],
            "latest_num": latest_num,
        })

    # Character and search character info for settings form.
    characters = g.db.query(Character).filter(Character.user_id == g.user.id).order_by(Character.title).all()
    character_shortcuts = {_.shortcut: _.id for _ in characters if _.shortcut is not None}
    search_character_groups = g.db.query(SearchCharacterGroup).order_by(
        SearchCharacterGroup.order,
    ).options(joinedload(SearchCharacterGroup.characters)).all()

    pm_chats = None
    if chat.type == "pm":
        # Fetch PMs list for the sidebar.
        # Join opposing ChatUser on PM chats so we know who the other person is.
        PMChatUser = aliased(ChatUser)
        pm_chats = g.db.query(ChatUser, PMChat, PMChatUser).filter(
            ChatUser.user_id == g.user.id,
            ChatUser.subscribed == True,
        ).join(
            PMChat,
            and_(
                PMChat.type == "pm",
                ChatUser.chat_id == PMChat.id,
            ),
        ).join(
            PMChatUser,
            and_(
                PMChatUser.chat_id == PMChat.id,
                PMChatUser.user_id != g.user.id,
            ),
        ).options(joinedload(PMChatUser.user)).order_by(
            PMChat.last_message.desc(),
        ).limit(50).all()

    return render_template(
        "rp/chat/chat.html",
        url=url,
        chat=chat_dict,
        chat_user=chat_user,
        chat_user_dict=chat_user.to_dict(include_options=True),
        messages=messages,
        latest_num=latest_num,
        case_options=case_options,
        characters=characters,
        character_shortcuts=character_shortcuts,
        search_character_groups=search_character_groups,
        pm_chats=pm_chats,
    )


@use_db
@get_chat
def log(chat, pm_user, url, fmt=None, page=None):

    chat_dict = chat.to_dict()

    if chat.type == "pm":
        # Override title with the other person's username.
        chat_dict['title'] = "Log with " + pm_user.username
        chat_dict['url'] = url

    try:
        own_chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.chat_id == chat.id,
            ChatUser.user_id == g.user.id,
        )).one()
    except:
        own_chat_user = None

    message_count = g.db.query(func.count('*')).select_from(Message).filter(
        Message.chat_id == chat.id,
    )
    if own_chat_user is not None and not own_chat_user.show_system_messages:
        message_count = message_count.filter(Message.type.in_(("ic", "ooc", "me")))
    message_count = message_count.scalar()

    messages_per_page = 200

    if page is None:
        # Default to last page.
        page = int(ceil(float(message_count) / messages_per_page))
        # The previous calculation doesn't work if pages have no messages.
        if page < 1:
            page = 1

    messages = g.db.query(Message).filter(
        Message.chat_id == chat.id,
    ).order_by(Message.id).options(
        joinedload(Message.chat_user),
    )
    if own_chat_user is not None and not own_chat_user.show_system_messages:
        messages = messages.filter(Message.type.in_(("ic", "ooc", "me")))
    messages = messages.limit(messages_per_page).offset((page - 1) * messages_per_page).all()

    if len(messages) == 0 and page != 1:
        return redirect(url_for("rp_log", url=url, fmt=fmt))

    if fmt == "json":

        return jsonify({
            "total": message_count,
            "messages": [_.to_dict() for _ in messages],
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=messages_per_page,
        item_count=message_count,
        url=lambda page: url_for("rp_log", url=url, page=page),
    )

    return render_template(
        "rp/chat/log.html",
        own_chat_user=own_chat_user,
        url=url,
        chat=chat,
        messages=messages,
        paginator=paginator,
    )


@alt_formats(set(["json"]))
@use_db
@log_in_required
@get_chat
def users(chat, pm_user, url, fmt=None, page=1):

    if chat.type != "group":
        abort(404)

    try:
        own_chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.chat_id == chat.id,
            ChatUser.user_id == g.user.id,
        )).one()
    except:
        own_chat_user = None

    user_count = g.db.query(func.count('*')).select_from(ChatUser).filter(
        ChatUser.chat_id == chat.id,
    ).scalar()

    users = g.db.query(ChatUser).filter(
        ChatUser.chat_id == chat.id,
    ).options(
        joinedload(ChatUser.user),
        joinedload_all("ban.creator_chat_user"),
    ).order_by(ChatUser.number).limit(20).offset((page - 1) * 20).all()

    if len(users) == 0:
        abort(404)

    if fmt == "json":
        return jsonify({
            "total": user_count,
            "users": [_.to_dict() for _ in users]
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=20,
        item_count=user_count,
        url=lambda page: url_for("rp_users", url=url, page=page),
    )

    return render_template(
        "rp/chat/chat_users.html",
        chat=chat,
        own_chat_user=own_chat_user,
        users=users,
        paginator=paginator,
    )


@use_db
@log_in_required
def unban(url):
    try:
        chat = g.db.query(GroupChat).filter(GroupChat.url == url).one()
        own_chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.chat_id == chat.id,
            ChatUser.user_id == g.user.id,
        )).one()
    except NoResultFound:
        abort(404)
    if not own_chat_user.can("ban"):
        abort(403)
    try:
        unban_chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.chat_id == chat.id,
            ChatUser.number == int(request.form["number"]),
        )).one()
    except (NoResultFound, ValueError):
        abort(404)
    try:
        ban = g.db.query(Ban).filter(and_(Ban.chat_id == chat.id, Ban.user_id == unban_chat_user.user_id)).one()
    except NoResultFound:
        abort(404)
    g.db.delete(ban)
    send_message(g.db, g.redis, Message(
        chat_id=chat.id,
        user_id=unban_chat_user.user_id,
        type="user_action",
        name=own_chat_user.name,
        text="%s [%s] unbanned %s [%s] from the chat." % (
            own_chat_user.name, own_chat_user.acronym,
            unban_chat_user.name, unban_chat_user.acronym,
        ),
    ))
    if "Referer" in request.headers:
        return redirect(request.headers["Referer"])
    return redirect(url_for("rp_chat_users", url=url))


def _alter_subscription(chat, pm_user, url, new_value):

    try:
        chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.user_id == g.user.id,
            ChatUser.chat_id == chat.id,
        )).one()
    except NoResultFound:
        abort(404)

    chat_user.subscribed = new_value

    if "X-Requested-With" in request.headers and request.headers["X-Requested-With"] == "XMLHttpRequest":
        return "", 204

    if "Referer" in request.headers:
        return redirect(request.headers["Referer"])
    return redirect(url_for("rp_chat", url=url))


@use_db
@log_in_required
@get_chat
def subscribe(chat, pm_user, url, fmt):
    return _alter_subscription(chat, pm_user, url, True)


@use_db
@log_in_required
@get_chat
def unsubscribe(chat, pm_user, url, fmt):
    return _alter_subscription(chat, pm_user, url, False)


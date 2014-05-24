from flask import Flask, abort, g, redirect, render_template, request, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm.exc import NoResultFound
from webhelpers import paginate

from charat2.helpers.auth import login_required
from charat2.model import (
    case_options,
    AnyChat,
    Ban,
    Chat,
    GroupChat,
    Message,
    PMChat,
    User,
    UserChat,
)
from charat2.model.connections import use_db
from charat2.model.validators import url_validator


@use_db
@login_required
def create_chat():
    # Silently truncate to 50 because we've got a maxlength on the <input>.
    url = request.form["url"][:50]
    # Change URL to lower case but remember the original case for the title.
    lower_url = url.lower()
    if url_validator.match(lower_url) is None:
        return render_template(
            "rp/home.html",
            create_chat_error="That URL isn't valid. Chat URLs can only "
            "contain letters, numbers, hyphens and underscores."
        )
    # Don't allow pm because subchats of it (pm/*) will crash into private
    # chat URLs.
    if url=="pm" or g.db.query(Chat.id).filter(Chat.url==lower_url).count()!=0:
        return render_template(
            "rp/home.html",
            create_chat_error="The URL \"%s\" has already been taken." % url
        )
    g.db.add(GroupChat(
        url=lower_url,
        title=url.replace("_", " "),
        creator_id=g.user.id,
    ))
    return redirect(url_for("chat", url=lower_url))


@use_db
@login_required
def chat(url):

    # Do some special URL stuff for PM chats.
    if url == "pm":

        abort(404)

    elif url.startswith("pm/"):

        username = url[3:]
        if username == "":
            abort(404)

        try:
            pm_user = g.db.query(User).filter(
                func.lower(User.username) == username.lower()
            ).one()
        except NoResultFound:
            abort(404)

        # You can't PM yourself.
        if pm_user == g.user:
            abort(404)

        if pm_user.username != username:
            return redirect(url_for("chat", url="pm/"+pm_user.username))

        # PM
        pm_url = "pm/" + ("/".join(sorted([str(g.user.id), str(pm_user.id)])))
        try:
            chat = g.db.query(PMChat).filter(
                PMChat.url==pm_url,
            ).one()
        except NoResultFound:
            chat = PMChat(url=pm_url)
            g.db.add(chat)
            g.db.flush()

        # Override title with the other person's username.
        chat_dict = chat.to_dict()
        chat_dict['title'] = "Messaging "+pm_user.username

    else:

        # Force lower case.
        if url != url.lower():
            return redirect(url_for("chat", url=url.lower()))

        try:
            chat = g.db.query(AnyChat).filter(AnyChat.url==url).one()
        except NoResultFound:
            abort(404)

        # Redirect them to the oubliette if they're banned.
        if g.db.query(func.count('*')).select_from(Ban).filter(and_(
            Ban.chat_id==chat.id,
            Ban.user_id==g.user.id,
        )).scalar() != 0:
            if chat.url != "theoubliette":
                return redirect(url_for("chat", url="theoubliette"))
            abort(403)

        chat_dict = chat.to_dict()

    # Get or create UserChat.
    try:
        user_chat = g.db.query(UserChat).filter(and_(
            UserChat.user_id==g.user.id,
            UserChat.chat_id==chat.id,
        )).one()
    except NoResultFound:
        user_chat = UserChat.from_user(g.user, chat_id=chat.id)
        if (
            chat.type == "group" and chat.autosilence
            and g.user.group != "admin" and g.user != chat.creator
        ):
            user_chat.group = "silent"
        g.db.add(user_chat)
        g.db.flush()

    # Show the last 50 messages.
    messages = g.db.query(Message).filter(
        Message.chat_id==chat.id,
    ).order_by(Message.posted.desc()).limit(50).all()
    messages.reverse()

    latest_num = messages[-1].id if len(messages) > 0 else 0
    
    logged_in = False
    if g.user is not None:
        logged_in = True

    return render_template(
        "rp/chat.html",
        url=url,
        chat=chat_dict,
        user_chat=user_chat,
        user_chat_dict=user_chat.to_dict(include_options=True),
        messages=messages,
        latest_num=latest_num,
        case_options=case_options,
        logged_in=logged_in
    )


@use_db
@login_required
def log(url, page=None):

    # Do some special URL stuff for PM chats.
    if url == "pm":

        abort(404)

    elif url.startswith("pm/"):

        username = url[3:]
        if username == "":
            abort(404)

        try:
            pm_user = g.db.query(User).filter(
                func.lower(User.username) == username.lower()
            ).one()
        except NoResultFound:
            abort(404)

        # You can't PM yourself.
        if pm_user == g.user:
            abort(404)

        if pm_user.username != username:
            return redirect(url_for("log", url="pm/"+pm_user.username))

        # PM
        pm_url = "pm/" + ("/".join(sorted([str(g.user.id), str(pm_user.id)])))
        try:
            chat = g.db.query(PMChat).filter(
                PMChat.url==pm_url,
            ).one()
        except NoResultFound:
            abort(404)
            
        # Override title with the other person's username.
        chat_dict = chat.to_dict()
        chat_dict['title'] = "Log With "+pm_user.username

    else:

        try:
            chat = g.db.query(AnyChat).filter(AnyChat.url==url).one()
        except NoResultFound:
            abort(404)

    if page is None:
        page = 1

    messages = g.db.query(Message).filter(
        Message.chat_id==chat.id,
    ).order_by(Message.id).limit(100).offset((page-1)*100).all()

    if len(messages) == 0:
        abort(404)

    message_count = g.db.query(func.count('*')).select_from(Message).filter(
        Message.chat_id==chat.id,
    ).scalar()
    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=100,
        item_count=message_count,
        url=lambda page: url_for("log", url=url, page=page),
    )

    return render_template(
        "rp/log.html",
        url=url,
        chat=chat,
        messages=messages,
        paginator=paginator,
    )


from flask import abort, g, redirect, render_template, request, url_for
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.auth import login_required
from charat2.model import (
    case_options,
    AnyChat,
    Chat,
    GroupChat,
    Message,
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
            "home.html",
            create_chat_error="That URL isn't valid. Chat URLs can only "
            "contain letters, numbers, hyphens and underscores."
        )
    # Don't allow pm because subchats of it (pm/*) will crash into private
    # chat URLs.
    if url=="pm" or g.db.query(Chat.id).filter(Chat.url==lower_url).count()!=0:
        return render_template(
            "home.html",
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
    # PM chats aren't implemented yet so just 404 them for now.
    if url=="pm" or url.startswith("pm/"):
        abort(404)
    try:
        chat = g.db.query(AnyChat).filter(AnyChat.url==url).one()
    except NoResultFound:
        abort(404)
    try:
        user_chat = g.db.query(UserChat).filter(and_(
            UserChat.user_id==g.user.id,
            UserChat.chat_id==chat.id,
        )).one()
    except NoResultFound:
        user_chat = UserChat.from_user(g.user, chat_id=chat.id)
        g.db.add(user_chat)
        g.db.flush()
    messages = g.db.query(Message).filter(
        Message.chat_id==chat.id,
    ).order_by(Message.posted.desc()).limit(50).all()
    messages.reverse()
    latest_num = messages[-1].id if len(messages) > 0 else 0
    return render_template(
        "chat.html",
        chat=chat,
        user_chat=user_chat,
        user_chat_dict=user_chat.to_dict(include_options=True),
        messages=messages,
        latest_num=latest_num,
        case_options=case_options,
    )


from flask import abort, g, redirect, render_template, url_for
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from charat2.model import AnyChat, UserChat
from charat2.model.validators import url_validator

def chat(url):
    # Redirect to the homepage if they're not logged in. We'll sort out guest
    # users later.
    if g.user is None:
        return redirect(url_for("home"))
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
        # XXX COPY CHARACTER INFO FROM USER
        user_chat = UserChat(user_id=g.user.id, chat_id=chat.id)
        g.db.add(user_chat)
        g.db.flush()
    return render_template("chat.html", chat=chat, user_chat=user_chat)


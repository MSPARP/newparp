from flask import abort, g, request
from functools import wraps
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4

from charat2.model import AnyChat, User, UserChat

def get_request_user():
    g.user = None
    if "session" in request.cookies:
        g.session_id = request.cookies["session"]
        user_id = g.redis.get("session:" + g.session_id)
        if user_id is not None:
            try:
                g.user = g.db.query(User).filter(User.id==user_id).one()
            except NoResultFound:
                pass
    else:
        g.session_id = str(uuid4())

def set_cookie(response):
    if not "session" in request.cookies:
        # XXX SET DOMAIN
        response.set_cookie("session", g.session_id, max_age=365*24*60*60)
    return response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def user_chat_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Fetch Chat and UserChat objects.
        # They must already exist (ie. we must have hit the chat page before
        # requesting anything from this view).
        if g.user is None:
            abort(403)
        if "chat_id" not in request.form:
            abort(400)
        try:
            g.user_chat, g.chat = g.db.query(
                UserChat, AnyChat,
            ).join(
                AnyChat, UserChat.chat_id==AnyChat.id,
            ).filter(and_(
                UserChat.user_id==g.user.id,
                UserChat.chat_id==request.form["chat_id"],
            )).one()
        except NoResultFound:
            abort(400)
        return f(*args, **kwargs)
    return decorated_function


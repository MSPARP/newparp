import os

from datetime import datetime
from flask import abort, g, redirect, request
from functools import wraps
from redis import ConnectionPool, StrictRedis
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4

from charat2.model import sm, AnyChat, User, ChatUser

redis_pool = ConnectionPool(
    host=os.environ['REDIS_HOST'],
    port=int(os.environ['REDIS_PORT']),
    db=int(os.environ['REDIS_DB']),
)

cookie_domain = "." + os.environ['BASE_DOMAIN']


def set_cookie(response):
    if "session" not in request.cookies:
        # XXX SET DOMAIN
        response.set_cookie(
            "session",
            g.session_id,
            max_age=365 * 24 * 60 * 60,
            domain=cookie_domain,
        )
    return response


# Pre- and post-request handlers for the Redis connection.
# Automatically get session's user ID too because we're always gonna need it.


def redis_connect():
    g.redis = StrictRedis(connection_pool=redis_pool)
    if "session" in request.cookies:
        g.session_id = request.cookies["session"]
        g.user_id = g.redis.get("session:" + g.session_id)
    else:
        g.session_id = str(uuid4())
        g.user_id = None


def redis_disconnect(response):
    del g.redis
    return response


# Connection function and decorators for connecting to the database.
# The first decorator just fetches the User object and is for general stuff.
# The second fetches the User, ChatUser and Chat objects and is used by the
# chat-related views.
# (also the second is in a function by itself so it can be called by
# mark_alive too)


def db_connect():
    if not hasattr(g, "db"):
        g.db = sm()


def use_db(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db_connect()
        g.user = None
        if g.user_id is not None:
            try:
                g.user = g.db.query(User).filter(User.id == g.user_id).one()
            except NoResultFound:
                pass
            g.user.last_online = datetime.now()
            g.user.last_ip = request.headers["X-Forwarded-For"]
            if g.user.group == "banned":
                return redirect("http://rp.terminallycapricio.us/")
        return f(*args, **kwargs)
    return decorated_function


def get_chat_user():
    try:
        g.chat_user, g.user, g.chat = g.db.query(
            ChatUser, User, AnyChat,
        ).join(
            User, ChatUser.user_id == User.id,
        ).join(
            AnyChat, ChatUser.chat_id == AnyChat.id,
        ).filter(and_(
            ChatUser.user_id == g.user_id,
            ChatUser.chat_id == int(request.form["chat_id"]),
        )).one()
    except NoResultFound:
        abort(400)
    g.user.last_online = datetime.now()
    g.user.last_ip = request.headers["X-Forwarded-For"]
    if g.user.group == "banned":
        abort(403)


def use_db_chat(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db_connect()
        get_chat_user()
        return f(*args, **kwargs)
    return decorated_function


# Post-request handlers for committing and disconnecting.
# Disconnect is run on every request and commit is run on every successful
# request.

# They skip if there isn't a database connection because not all requests will
# be connecting to the database.


def db_commit(response=None):
    # Don't commit on 4xx and 5xx.
    if response is not None and response.status[0] not in {"2", "3"}:
        return response
    if hasattr(g, "db"):
        g.db.commit()
    return response


def db_disconnect(response=None):
    if hasattr(g, "db"):
        g.db.close()
        del g.db
    return response


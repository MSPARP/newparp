import os

from contextlib import contextmanager
from datetime import datetime
from flask import abort, g, redirect, request
from functools import wraps
from redis import ConnectionPool, StrictRedis
from sqlalchemy import and_, func
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4

from newparp.model import sm, AnyChat, Chat, ChatUser, User
from newparp.helpers.users import queue_user_meta, get_ip_banned


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = sm()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


redis_pool = ConnectionPool(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    db=int(os.environ["REDIS_DB"]),
    decode_responses=True,
)

cookie_domain = "." + os.environ["BASE_DOMAIN"]


def set_cookie(response):
    if "newparp" not in request.cookies:
        response.set_cookie(
            "newparp",
            g.session_id,
            max_age=365 * 24 * 60 * 60,
            domain=cookie_domain if "localhost" not in cookie_domain.lower() else None,
        )
    return response


# Pre- and post-request handlers for the Redis connection.
# Automatically get session's user ID too because we're always gonna need it.


def redis_connect():
    g.redis = StrictRedis(connection_pool=redis_pool)
    if "newparp" in request.cookies:
        g.session_id = request.cookies["newparp"]
        g.user_id = g.redis.get("session:" + g.session_id)
        if g.user_id is not None:
            g.redis.expire("session:" + g.session_id, 2592000)
            g.user_id = int(g.user_id)
    else:
        g.session_id = str(uuid4())
        g.user_id = None
    g.csrf_token = g.redis.get("session:%s:csrf" % g.session_id)
    expiry_time = 86400 if g.user_id is not None else 3600
    if g.csrf_token is None:
        g.csrf_token = str(uuid4())
        g.redis.set("session:%s:csrf" % g.session_id, g.csrf_token, expiry_time)
    else:
        g.redis.expire("session:%s:csrf" % g.session_id, expiry_time)


def redis_disconnect(response):
    if hasattr(g, "pubsub"):
        g.pubsub.close()
        del g.pubsub

    if hasattr(g, "redis"):
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
                return f(*args, **kwargs)
            queue_user_meta(g, g.redis, request.headers.get("X-Forwarded-For", request.remote_addr))
            g.unread_chats = g.db.query(func.count('*')).select_from(ChatUser).join(Chat).filter(and_(
                ChatUser.user_id == g.user.id,
                ChatUser.subscribed == True,
                Chat.last_message > ChatUser.last_online,
            )).scalar()
            if g.user.group == "banned":
                return redirect("http://rp.terminallycapricio.us/")
        g.ip_banned = get_ip_banned(request.headers.get("X-Forwarded-For", request.remote_addr), g.db, g.redis)
        if g.ip_banned and (g.user is None or not g.user.is_admin):
            return redirect("http://pup-king-louie.tumblr.com/")
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
    queue_user_meta(g, g.redis, request.headers.get("X-Forwarded-For", request.remote_addr))
    if g.user.group != "active":
        abort(403)
    g.ip_banned = get_ip_banned(request.headers.get("X-Forwarded-For", request.remote_addr), g.db, g.redis)
    if g.ip_banned and not g.user.is_admin:
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


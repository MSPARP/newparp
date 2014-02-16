import json
import time

from flask import abort, g
from functools import wraps
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from charat2.model import Message, UserChat

def mark_alive(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        online = g.redis.sismember("chat:%s:online" % g.chat.id, g.user.id)
        if not online:
            g.redis.sadd("chat:%s:online" % g.chat.id, g.user.id)
            send_message(g.db, g.redis, Message(
                chat_id=g.chat.id,
                type="join",
                text="%s [%s] joined chat." % (
                    g.user_chat.name, g.user_chat.acronym,
                ),
            ))
        g.redis.zadd(
            "chats_alive",
            time.time()+15,
            "%s/%s" % (g.chat.id, g.user.id),
        )
        return f(*args, **kwargs)
    return decorated_function

def send_message(db, redis, message):
    db.add(message)
    db.flush()
    redis_message = {
        "messages": [message.to_dict()],
    }
    # Reload userlist if necessary.
    if message.type in (
        u"join",
        u"disconnect",
        u"timeout",
        u"user_info",
        u"user_group",
        u"user_action",
    ):
        redis_message["users"] = get_userlist(db, redis, message.chat)
    redis.publish("channel:%s" % message.chat_id, json.dumps(redis_message))

def disconnect(redis, chat_id, user_id):
	redis.zrem("chats_alive", "%s/%s" % (chat_id, user_id))
    # Return True if they were in the userlist when we tried to remove them, so
    # we can avoid sending disconnection messages if someone gratuitously sends
    # quit requests.
	return (redis.srem("chat:%s:online" % chat_id, user_id) == 1)

def get_userlist(db, redis, chat):
    online_user_ids = redis.smembers("chat:%s:online" % chat.id)
    # Don't bother querying if the list is empty.
    if len(online_user_ids) == 0:
        return []
    return [
        _.to_dict() for _ in
        db.query(UserChat).filter(and_(
            UserChat.user_id.in_(online_user_ids),
            UserChat.chat_id == chat.id,
        )).options(joinedload(UserChat.user))
    ]


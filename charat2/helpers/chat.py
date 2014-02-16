import json
import time

from flask import abort, g
from functools import wraps

from charat2.model import Message

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
    redis.publish("channel.%s" % message.chat_id, json.dumps({
        "messages": [message.to_dict()],
    }))


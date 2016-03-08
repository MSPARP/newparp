import time
import json

from celery.utils.log import get_task_logger
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.chat import disconnect, send_message, send_userlist
from charat2.model import Message, ChatUser
from charat2.tasks import celery, WorkerTask

logger = get_task_logger(__name__)


# Make sure a message is sent every 25 seconds so the long poll requests
# don't time out.
# XXX INCREASE THIS TO SEVERAL MINUTES
@celery.task(base=WorkerTask, queue="worker")
def ping_longpolls():
    redis = ping_longpolls.redis

    current_time = int(time.time())

    for chat_id in redis.zrangebyscore("longpoll_timeout", 0, current_time):
        redis.publish("channel:%s" % chat_id, "{\"messages\":[]}")
        if redis.hlen("chat:%s:online" % chat_id) != 0:
            redis.zadd("longpoll_timeout", time.time() + 25, chat_id)
        else:
            redis.zrem("longpoll_timeout", chat_id)


@celery.task(base=WorkerTask, queue="worker")
def reap():
    redis = reap.redis
    db = reap.db

    current_time = int(time.time())
    disconnected_users = set()

    # Long poll sessions.
    for dead in redis.zrangebyscore("chats_alive", 0, current_time):
        logger.info("Reaping %s" % dead)
        chat_id, session_id = dead.split('/')
        user_id = redis.hget("chat:%s:online" % chat_id, session_id)
        disconnected = disconnect(redis, chat_id, session_id)
        # Only send a timeout message if they were already online.
        if not disconnected:
            logger.info("Not sending timeout message.")
            continue
        disconnected_users.add((chat_id, user_id, False))

    # Sockets.
    for dead in redis.zrangebyscore("sockets_alive", 0, current_time):
        logger.info("Reaping %s" % dead)
        chat_id, session_id, socket_id = dead.split('/')
        user_id = redis.hget("chat:%s:online" % chat_id, socket_id)
        disconnected = disconnect(redis, chat_id, socket_id)
        redis.srem("chat:%s:sockets:%s" % (chat_id, session_id), socket_id)
        redis.zrem("sockets_alive", "%s/%s/%s" % (chat_id, session_id, socket_id))
        # Only send a timeout message if they were already online.
        if not disconnected:
            logger.info("Not sending timeout message.")
            continue
        disconnected_users.add((chat_id, user_id, True))

    for chat_id, user_id, reaped_socket in disconnected_users:
        try:
            dead_chat_user = db.query(ChatUser).filter(and_(
                ChatUser.user_id == user_id,
                ChatUser.chat_id == chat_id,
            )).options(joinedload(ChatUser.chat), joinedload(ChatUser.user)).one()
        except NoResultFound:
            logger.error("Unable to find ChatUser (chat %s, user %s)." % (chat_id, user_id))
            continue

        if reaped_socket:
            typing_key = "chat:%s:typing" % chat_id
            if redis.srem(typing_key, dead_chat_user.number):
                redis.publish("channel:%s:typing" % chat_id, json.dumps({
                    "typing": list(int(_) for _ in redis.smembers(typing_key)),
                }))

        if dead_chat_user.computed_group == "silent" or dead_chat_user.chat.type in ("pm", "roulette"):
            send_userlist(db, redis, dead_chat_user.chat)
        else:
            send_message(db, redis, Message(
                chat_id=chat_id,
                user_id=dead_chat_user.user_id,
                type="timeout",
                name=dead_chat_user.name,
                text="%s's connection timed out." % dead_chat_user.name,
            ))
        logger.info("Sent timeout message for ChatUser (chat %s, user %s)." % (chat_id, user_id))

    db.commit()


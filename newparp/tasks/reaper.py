import time
import json

from celery.utils.log import get_task_logger
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from newparp.helpers.chat import disconnect, send_message, send_userlist
from newparp.model import Message, ChatUser
from newparp.model.connections import session_scope, NewparpRedis, redis_chat_pool
from newparp.model.user_list import UserListStore
from newparp.tasks import celery, WorkerTask

logger = get_task_logger(__name__)


@celery.task(base=WorkerTask, queue="worker")
def reap():
    redis_chat = NewparpRedis(connection_pool=redis_chat_pool)
    for chat_id in UserListStore.scan_active_chats(redis_chat):
        reap_chat.delay(chat_id)


@celery.task(base=WorkerTask, queue="worker")
def reap_chat(chat_id):
    raise NotImplementedError


@celery.task(base=WorkerTask, queue="worker")
def old_reap():
    redis = reap.redis
    with session_scope() as db:
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


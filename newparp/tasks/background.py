import datetime
import json

from celery.utils.log import get_task_logger
from sqlalchemy import and_

from newparp.model import Chat, ChatUser, GroupChat, User
from newparp.model.connections import session_scope, NewparpRedis, redis_chat_pool
from newparp.model.user_list import UserListStore
from newparp.tasks import celery, WorkerTask

logger = get_task_logger(__name__)


@celery.task(base=WorkerTask, queue="worker")
def generate_counters():
    logger.info("Generating user counters.")
    redis_chat = NewparpRedis(connection_pool=redis_chat_pool)

    user_ids_online = list(UserListStore.multi_user_ids_online(
        redis_chat,
        UserListStore.scan_active_chats(redis_chat),
    ))

    generate_counters.redis.set(
        "connected_users",
        len(set.union(*user_ids_online)) if user_ids_online else 0,
    )


@celery.task(base=WorkerTask, queue="worker")
def unlist_chats():
    with session_scope() as db:
        db.query(GroupChat).filter(and_(
            GroupChat.id == Chat.id,
            GroupChat.publicity == "listed",
            GroupChat.last_message < datetime.datetime.now() - datetime.timedelta(7)
        )).update({"publicity": "unlisted"})
        db.commit()


@celery.task(base=WorkerTask, queue="worker")
def update_lastonline():
    redis = update_lastonline.redis

    if redis.exists("lock:lastonline"):
        return
    redis.setex("lock:lastonline", 60, 1)

    chat_ids = redis.hgetall("queue:lastonline")

    # Reset the list for the next iteration.
    redis.delete("queue:lastonline")

    for chat_id, posted in chat_ids.items():
        online_user_ids = set(int(_) for _ in redis.hvals("chat:%s:online" % chat_id))

        try:
            posted = datetime.datetime.utcfromtimestamp(float(posted))
        except ValueError:
            continue

        with session_scope() as db:
            db.query(Chat).filter(Chat.id == chat_id).update({"last_message": posted}, synchronize_session=False)
            if len(online_user_ids) != 0:
                db.query(ChatUser).filter(and_(
                    ChatUser.user_id.in_(online_user_ids),
                    ChatUser.chat_id == chat_id,
                )).update({"last_online": posted}, synchronize_session=False)

    redis.delete("lock:lastonline")


@celery.task(base=WorkerTask, queue="worker")
def update_user_meta():
    redis = update_user_meta.redis

    if redis.exists("lock:metaupdate"):
        return
    redis.setex("lock:metaupdate", 60, 1)

    meta_updates = redis.hgetall("queue:usermeta")

    # Reset the list for the next iteration.
    redis.delete("queue:usermeta")

    for key, meta in meta_updates.items():
        try:
            meta = json.loads(meta)
        except ValueError:
            continue

        msgtype, userid = key.split(":", 2)

        with session_scope() as db:
            if msgtype == "user" and "last_ip" in meta:
                try:
                    last_online = datetime.datetime.utcfromtimestamp(float(meta["last_online"]))
                except (ValueError, KeyError):
                    last_online = datetime.datetime.now()

                db.query(User).filter(User.id == userid).update({
                    "last_online": last_online,
                    "last_ip": meta["last_ip"]
                }, synchronize_session=False)
            elif msgtype == "chatuser":
                try:
                    last_online = datetime.datetime.utcfromtimestamp(float(meta["last_online"]))
                except (ValueError, KeyError):
                    last_online = datetime.datetime.now()

                db.query(ChatUser).filter(and_(ChatUser.user_id == userid, ChatUser.chat_id == meta["chat_id"])).update({
                    "last_online": last_online
                }, synchronize_session=False)

    redis.delete("lock:metaupdate")

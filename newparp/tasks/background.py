import datetime

from celery.utils.log import get_task_logger
from sqlalchemy import and_

from newparp.model import Chat, ChatUser, GroupChat
from newparp.tasks import celery, WorkerTask

logger = get_task_logger(__name__)


@celery.task(base=WorkerTask, queue="worker")
def generate_counters():
    redis = generate_counters.redis

    logger.info("Generating user counters.")

    # Online user counter
    connected_users = set()
    next_index = 0
    while True:
        next_index, keys = redis.scan(next_index, "chat:*:online")
        for key in keys:
            for user_id in redis.hvals(key):
                connected_users.add(user_id)
        if int(next_index) == 0:
            break
    redis.set("connected_users", len(connected_users))


@celery.task(base=WorkerTask, queue="worker")
def unlist_chats():
    unlist_chats.db.query(GroupChat).filter(and_(
        GroupChat.id == Chat.id,
        GroupChat.publicity == "listed",
        GroupChat.last_message < datetime.datetime.now() - datetime.timedelta(7)
    )).update({"publicity": "unlisted"})
    unlist_chats.db.commit()


@celery.task(base=WorkerTask, queue="worker")
def update_lastonline():
    db = update_lastonline.db
    redis = update_lastonline.redis

    chat_ids = redis.hgetall("queue:lastonline")

    # Reset the list for the next iteration.
    redis.delete("queue:lastonline")

    for chat_id, posted in chat_ids.items():
        online_user_ids = set(int(_) for _ in redis.hvals("chat:%s:online" % chat_id))

        try:
            posted = datetime.datetime.utcfromtimestamp(float(posted))
        except ValueError:
            continue

        db.query(Chat).filter(Chat.id == chat_id).update({"last_message": posted}, synchronize_session=False)

        if len(online_user_ids) != 0:
            db.query(ChatUser).filter(and_(
                ChatUser.user_id.in_(online_user_ids),
                ChatUser.chat_id == chat_id,
            )).update({"last_online": posted}, synchronize_session=False)

        db.commit()

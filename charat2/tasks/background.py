import datetime

from celery.utils.log import get_task_logger
from sqlalchemy import and_

from charat2.model import Chat, ChatUser, GroupChat
from charat2.tasks import celery, WorkerTask

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

    # Searching counter
    searching_users = set()
    for searcher_id in redis.smembers("searchers"):
        session_id = redis.get("searcher:%s:session_id" % searcher_id)
        user_id = redis.get("session:%s" % session_id)
        if user_id is not None:
            searching_users.add(user_id)
    redis.set("searching_users", len(searching_users))

    # Roulette counter
    rouletting_users = set()
    for searcher_id in redis.smembers("roulette_searchers"):
        session_id = redis.get("roulette:%s:session_id" % searcher_id)
        user_id = redis.get("session:%s" % session_id)
        if user_id is not None:
            rouletting_users.add(user_id)
    redis.set("rouletting_users", len(rouletting_users))


@celery.task(base=WorkerTask)
def unlist_chats():
    unlist_chats.db.query(GroupChat).filter(and_(
        GroupChat.id == Chat.id,
        GroupChat.publicity == "listed",
        GroupChat.last_message < datetime.datetime.now() - datetime.timedelta(7)
    )).update({"publicity": "unlisted"})
    unlist_chats.db.commit()


@celery.task(base=WorkerTask)
def update_lastonline():
    db = update_lastonline.db
    redis = update_lastonline.redis

    chat_ids = redis.hgetall("queue:lastonline")

    # Reset the list for the next iteration.
    redis.delete("queue:lastonline")

    for chat_id, posted in chat_ids.iteritems():
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

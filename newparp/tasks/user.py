from celery.utils.log import get_task_logger
from sqlalchemy import func, and_

from newparp.model import Chat, ChatUser
from newparp.tasks import celery, WorkerTask

logger = get_task_logger(__name__)


@celery.task(base=WorkerTask)
def update_unread_chats(user_id):
    db = update_unread_chats.db
    redis = update_unread_chats.redis

    logger.debug("Updating unread chats for user %s", user_id)
    unread_chats = db.query(ChatUser).join(Chat).filter(and_(
        ChatUser.user_id == user_id,
        ChatUser.subscribed == True,
        Chat.last_message > ChatUser.last_online,
    )).all()
    logger.debug("%s unread chats for user %s", len(unread_chats), user_id)

    for chat in unread_chats:
        redis.sadd("user:%s:unread" % (user_id), chat.chat_id)
    redis.expire("user:%s:unread" % (user_id), 86400)
    redis.set("user:%s:unread:generated" % (user_id), 3600)


@celery.task(base=WorkerTask)
def set_unread_chat(chat_id):
    db = set_unread_chat.db
    redis = set_unread_chat.redis

    logger.debug("Updating unread cache for chat %s", chat_id)
    online_user_ids = set(int(_) for _ in redis.hvals("chat:%s:online" % chat_id))
    logger.debug("Ignored %s users", len(online_user_ids))

    for chat_user in db.query(ChatUser).filter(and_(
        ChatUser.chat_id == chat_id,
        ChatUser.subscribed == True,
    )):
        if chat_user.user_id in online_user_ids:
            continue

        redis.sadd("user:%s:unread" % (chat_user.user_id), chat_id)
        redis.expire("user:%s:unread" % (chat_user.user_id), 86400)


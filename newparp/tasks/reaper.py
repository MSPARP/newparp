from celery.utils.log import get_task_logger
from sqlalchemy import and_

from newparp.helpers.chat import send_message, send_userlist
from newparp.model import Chat, ChatUser, Message
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
    user_list = UserListStore(NewparpRedis(connection_pool=redis_chat_pool), chat_id)
    old_user_ids = user_list.user_ids_online()
    if not old_user_ids:
        return

    with session_scope() as db:
        chat = db.query(Chat).filter(Chat.id == chat_id).one()
        chat_users = {
            _.user_id: _
            for _ in db.query(ChatUser).filter(and_(
                ChatUser.chat_id == chat_id,
                ChatUser.user_id.in_(old_user_ids),
            ))
        }

        for socket_id, user_id in user_list.inconsistent_entries():
            chat_user = chat_users[user_id]
            dead = user_list.socket_disconnect(socket_id, chat_user.number)
            if dead:
                logger.debug("dead: %s" % chat_user)
                # TODO optimise this when reaping several people at once?
                if chat_user.computed_group == "silent" or chat.type in ("pm", "roulette"):
                    send_userlist(user_list, db, chat)
                else:
                    send_message(db, reap_chat.redis, Message(
                        chat=chat,
                        user_id=chat_user.user_id,
                        type="timeout",
                        name=chat_user.name,
                        text="%s's connection timed out." % chat_user.name,
                    ), user_list)

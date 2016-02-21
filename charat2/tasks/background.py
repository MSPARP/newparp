import datetime

from sqlalchemy import and_

from charat2.model import Chat, ChatUser, Message, GroupChat, LogPage
from charat2.tasks import celery, WorkerTask

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


@celery.task(base=WorkerTask)
def unlist_chats():
    unlist_chats.db.query(GroupChat).filter(and_(
        GroupChat.publicity == "listed",
        GroupChat.last_message < datetime.datetime.now() - datetime.timedelta(7)
    )).update({"publicity": "unlisted"})
    unlist_chats_db.commit()


@celery.task(base=WorkerTask, ignore_result=True)
def generate_logpages(chat_id):
    db = generate_logpages.db
    messages_per_page = 200

    if len(db.query(LogPage).filter(LogPage.chat_id == chat_id).all()) > 0:
        return

    page = 1
    lastid = 0

    while True:
        messages = db.query(Message.id).filter(
            Message.chat_id == chat_id,
        ).filter(
            Message.id > lastid
        ).order_by(
            Message.posted
        ).limit(
            messages_per_page
        ).all()

        if len(messages) < messages_per_page:
            break

        db.add(LogPage(
            chat_id=chat_id,
            page=page,
            offset=messages[-1][0]
        ))

        lastid = messages[-1][0]
        page += 1

    db.commit()


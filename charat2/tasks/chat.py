from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload

from charat2.model import LogMarker, Message
from charat2.tasks import celery, WorkerTask


@celery.task(base=WorkerTask)
def update_log_marker(chat_id):
    db = update_log_marker.db
    redis = update_log_marker.redis
    chat_id = int(chat_id)

    # Fetch the last log marker.
    last_log_marker = (
        db.query(LogMarker)
        .filter(and_(
            LogMarker.chat_id == chat_id,
            LogMarker.type == "page_with_system_messages",
        ))
        .options(joinedload(LogMarker.message))
        .order_by(LogMarker.number.desc()).first()
    )

    # See how much has happened since that marker.
    if last_log_marker:
        messages_since_last_marker = (
            db.query(func.count("*")).select_from(Message)
            .filter(and_(
                Message.chat_id == chat_id,
                Message.posted >= last_log_marker.message.posted,
            )).scalar()
        )
        print messages_since_last_marker
        # And create a new one if necessary.
        if messages_since_last_marker > 200:
            db.add(LogMarker(
                chat_id=chat_id,
                type="page_with_system_messages",
                number=last_log_marker.number + 1,
                message_id=(
                    db.query(Message.id)
                    .filter(Message.chat_id == chat_id)
                    .order_by(Message.posted.desc()).limit(1).scalar()
                ),
            ))

    # Or create initial log marker if there aren't any.
    else:
        first_message = (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.posted).first()
        )
        if first_message:
            db.add(LogMarker(
                chat_id=chat_id,
                type="page_with_system_messages",
                number=1,
                message_id=first_message.id,
            ))

    db.commit()


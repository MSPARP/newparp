from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload

from newparp.model import LogMarker, Message
from newparp.tasks import celery, WorkerTask


@celery.task(base=WorkerTask)
def update_log_marker(chat_id, log_marker_type="page_with_system_messages"):
    db = update_log_marker.db
    redis = update_log_marker.redis
    chat_id = int(chat_id)

    if log_marker_type == "page_without_system_messages":
        message_filter = and_(
            Message.chat_id == chat_id,
            Message.type.in_(("ic", "ooc", "me")),
        )
    else:
        message_filter = Message.chat_id == chat_id

    # Fetch the last log marker.
    last_log_marker = (
        db.query(LogMarker)
        .filter(and_(
            LogMarker.chat_id == chat_id,
            LogMarker.type == log_marker_type,
        ))
        .options(joinedload(LogMarker.message))
        .order_by(LogMarker.number.desc()).first()
    )

    # See how much has happened since that marker.
    if last_log_marker:
        messages_since_last_marker = (
            db.query(func.count("*")).select_from(Message)
            .filter(and_(
                message_filter,
                Message.posted >= last_log_marker.message.posted,
            )).scalar()
        )
        # And create a new one if necessary.
        if messages_since_last_marker > 200:
            db.add(LogMarker(
                chat_id=chat_id,
                type=log_marker_type,
                number=last_log_marker.number + 1,
                message_id=(
                    db.query(Message.id)
                    .filter(and_(
                        message_filter,
                        Message.posted >= last_log_marker.message.posted,
                    )).order_by(Message.posted)
                    .offset(200).limit(1).scalar()
                ),
            ))

    # Or create initial log marker if there aren't any.
    else:
        first_message = (
            db.query(Message)
            .filter(message_filter)
            .order_by(Message.posted).first()
        )
        if first_message:
            db.add(LogMarker(
                chat_id=chat_id,
                type=log_marker_type,
                number=1,
                message_id=first_message.id,
            ))

    db.commit()


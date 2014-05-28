from flask import g, render_template, url_for
from sqlalchemy import and_
from sqlalchemy.orm import aliased, joinedload

from charat2.helpers.auth import login_required
from charat2.model import (
    case_options,
    AnyChat,
    UserChat,
)
from charat2.model.connections import use_db

@use_db
@login_required
def chat_list():

    PMUserChat = aliased(UserChat)
    chats = g.db.query(UserChat, AnyChat, PMUserChat).join(AnyChat).outerjoin(
        PMUserChat,
        and_(
            AnyChat.type == "pm",
            PMUserChat.chat_id == AnyChat.id,
            PMUserChat.user_id != g.user.id,
        ),
    ).options(joinedload(PMUserChat.user)).filter(
        UserChat.user_id == g.user.id,
    ).order_by(AnyChat.last_message.desc()).limit(50).all()

    return render_template(
        "rp/chat_list.html",
        chats=chats,
    )


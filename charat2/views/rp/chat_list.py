from flask import g, render_template, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased, joinedload
from webhelpers import paginate

from charat2.helpers.auth import login_required
from charat2.model import (
    case_options,
    AnyChat,
    UserChat,
)
from charat2.model.connections import use_db

@use_db
@login_required
def chat_list(page=1):

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
    ).order_by(
        AnyChat.last_message.desc(),
    ).offset((page-1)*50).limit(50).all()

    if len(chats) == 0:
        abort(404)

    chat_count = g.db.query(func.count('*')).select_from(UserChat).filter(
        UserChat.user_id==g.user.id,
    ).scalar()

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=chat_count,
        url=lambda page: url_for("chat_list", page=page),
    )

    return render_template(
        "rp/chat_list.html",
        chats=chats,
        paginator=paginator,
    )


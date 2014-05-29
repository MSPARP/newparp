from flask import abort, g, jsonify, render_template, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased, joinedload
from webhelpers import paginate

from charat2.helpers import alt_formats
from charat2.helpers.auth import login_required
from charat2.model import (
    case_options,
    AnyChat,
    GroupChat,
    OneOnOneChat,
    PMChat,
    UserChat,
)
from charat2.model.connections import use_db

chat_classes = {
    None: AnyChat,
    "group": GroupChat,
    "1-on-1": OneOnOneChat,
    "pm": PMChat,
    "unread": AnyChat,
}

@alt_formats(set(["json"]))
@use_db
@login_required
def chat_list(fmt=None, type=None, page=1):

    try:
        ChatClass = chat_classes[type]
    except KeyError:
        abort(404)

    if type in (None, "pm", "unread"):

        # Join opposing UserChat on PM chats so we know who the other person is.
        PMUserChat = aliased(UserChat)
        chats = g.db.query(UserChat, ChatClass, PMUserChat).join(ChatClass).outerjoin(
            PMUserChat,
            and_(
                ChatClass.type == "pm",
                PMUserChat.chat_id == ChatClass.id,
                PMUserChat.user_id != g.user.id,
            ),
        ).options(joinedload(PMUserChat.user))

        if type == "pm":
            chats = chats.filter(ChatClass.type == "pm")
        elif type == "unread":
            chats = chats.filter(ChatClass.last_message > UserChat.last_online)

    else:

        chats = g.db.query(UserChat, ChatClass).join(ChatClass).filter(
            ChatClass.type == type,
        )

    chats = chats.filter(
        UserChat.user_id == g.user.id,
    ).order_by(
        ChatClass.last_message.desc(),
    ).offset((page-1)*50).limit(50).all()

    if len(chats) == 0 and page != 1:
        abort(404)

    chat_count = g.db.query(func.count('*')).select_from(UserChat).filter(
        UserChat.user_id==g.user.id,
    )
    if type == "unread":
        chat_count = chat_count.join(ChatClass).filter(
            ChatClass.last_message > UserChat.last_online,
        )
    elif type is not None:
        chat_count = chat_count.join(ChatClass).filter(ChatClass.type == type)
    chat_count = chat_count.scalar()

    chat_dicts = []
    for c in chats:
        cd = c[1].to_dict()
        if c[1].type == "pm":
            cd["title"] = "Messaging "+c[2].user.username
            cd["url"] = "pm/"+c[2].user.username
        elif c[1].type != "group":
            cd["title"] = cd["url"]
        cd["unread"] = c[1].last_message > c[0].last_online
        chat_dicts.append(cd)

    if fmt == "json":

        return jsonify({
            "chat_count": chat_count,
            "chats": chat_dicts,
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=chat_count,
        url=lambda page: url_for("chat_list", page=page, type=type),
    )

    return render_template(
        "rp/chat_list.html",
        type=type,
        chats=chat_dicts,
        paginator=paginator,
    )


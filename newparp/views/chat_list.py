import paginate

from flask import abort, g, jsonify, render_template, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm import aliased, joinedload

from newparp.helpers import alt_formats
from newparp.helpers.auth import activation_required
from newparp.model import (
    case_options,
    AnyChat,
    GroupChat,
    RouletteChat,
    SearchedChat,
    PMChat,
    ChatUser,
)
from newparp.model.connections import use_db

chat_classes = {
    "all": AnyChat,
    "group": GroupChat,
    "pm": PMChat,
    "roulette": RouletteChat,
    "searched": SearchedChat,
    "unread": AnyChat,
}


@alt_formats({"json"})
@use_db
@activation_required
def chat_list(fmt=None, type=None, page=1):
    if type is None:
        type = "all"

    try:
        ChatClass = chat_classes[type]
    except KeyError:
        abort(404)

    chats = g.db.query(ChatUser, ChatClass).join(ChatClass).filter(and_(
        ChatUser.user_id == g.user.id,
        ChatUser.subscribed == True,
    ))
    if type == "unread":
        chats = chats.filter(ChatClass.last_message > ChatUser.last_online)

    chats = chats.order_by(
        ChatClass.last_message.desc(),
    ).offset((page - 1) * 50).limit(50).all()

    if len(chats) == 0 and page != 1:
        abort(404)

    chat_count = g.db.query(func.count('*')).select_from(ChatUser).filter(and_(
        ChatUser.user_id == g.user.id,
        ChatUser.subscribed == True,
    ))
    if type == "unread":
        chat_count = chat_count.join(ChatClass).filter(
            ChatClass.last_message > ChatUser.last_online,
        )
    elif type is not None:
        chat_count = chat_count.join(ChatClass)
    chat_count = chat_count.scalar()

    pipeline = g.redis.pipeline()
    for c in chats:
        pipeline.hvals("chat:%s:online" % c[1].id)

    chat_dicts = []
    for (chat_user, chat), online_user_ids in zip(chats, pipeline.execute()):

        if chat.type == "pm":
            pm_chat_user = g.db.query(ChatUser).filter(and_(
                ChatUser.chat_id == chat.id,
                ChatUser.user_id != g.user.id,
            )).options(joinedload(ChatUser.user)).first()
        else:
            pm_chat_user = None

        cd = chat.to_dict(pm_user=pm_chat_user.user if pm_chat_user is not None else None)

        cd["online"] = len(set(online_user_ids))
        if chat.type == "pm":
            cd["partner_online"] = pm_chat_user.user.id in (int(_) for _ in online_user_ids)

        cd["unread"] = chat.last_message > chat_user.last_online

        chat_dicts.append({
            "chat_user": chat_user.to_dict(include_title_and_notes=True),
            "chat": cd,
        })

    if fmt == "json":

        return jsonify({
            "total": chat_count,
            "chats": chat_dicts,
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=chat_count,
        url_maker=lambda page: url_for("rp_chat_list", page=page, type=type),
    )

    return render_template(
        "chat_list.html",
        type=type,
        chats=chat_dicts,
        paginator=paginator,
        chat_classes=chat_classes,
    )


import os
import json
from flask import abort, g, jsonify, make_response, render_template, request, redirect, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from newparp.helpers import alt_formats
from newparp.helpers.auth import admin_required, log_in_required
from newparp.model import case_options, Character, GroupChat, SearchCharacter, SearchCharacterGroup, SearchCharacterChoice, User
from newparp.model.connections import use_db, db_connect


@use_db
def home():

    if g.user is None:
        return render_template("home_guest.html")

    mode = request.args.get("mode", g.user.last_search_mode)
    g.user.last_search_mode = mode

    characters = g.db.query(Character).filter(Character.user_id == g.user.id).order_by(Character.title).all()

    search_character_groups = g.db.query(SearchCharacterGroup).order_by(
        SearchCharacterGroup.order,
    ).options(joinedload(SearchCharacterGroup.characters)).all()

    if mode == "roulette":
        return render_template(
            "home_roulette.html",
            characters=characters,
            search_character_groups=search_character_groups,
        )

    elif mode == "search":
        picky = set(_[0] for _ in g.db.query(
            SearchCharacterChoice.search_character_id,
        ).filter(
            SearchCharacterChoice.user_id == g.user.id,
        ).all())
        return render_template(
            "home_search.html",
            characters=characters,
            search_character_groups=search_character_groups,
            case_options=case_options,
            replacements=json.loads(g.user.replacements),
            regexes=json.loads(g.user.regexes),
            User=User,
            picky=picky,
        )

    abort(404)


@alt_formats({"json"})
@use_db
def unread(fmt=None):

    if g.user is None:
        return ""

    if fmt == "json":
        return jsonify({
            "unread": g.unread_chats,
            "url":url_for("rp_chat_list", type="unread"),
        })

    return render_template(
        "account/unread.html",
    )

def redirect():

    if "url" in request.args:
        url = request.args["url"].strip()
        if not url.startswith("http:") or not url.startswith("https:"):
            url = "http://www.mspaintadventures.com/ACT6ACT6.php?s=6&p=009309"

    else:
        url = url
        
    return render_template(
        "chat/redirect.html",
        url=url,
    )

@alt_formats({"json"})
@use_db
def groups(fmt=None):

    style_filter = set()
    for style in GroupChat.style.type.enums:
        if style in request.args:
            style_filter.add(style)
    if not style_filter:
        if g.user is not None:
            style_filter = g.user.group_chat_styles
        else:
            style_filter.add("script")

    level_filter = set()
    for level in GroupChat.level.type.enums:
        if level in request.args:
            level_filter.add(level)
    if not level_filter:
        if g.user is not None:
            level_filter = g.user.group_chat_levels
        else:
            level_filter.add("sfw")

    if g.user is not None:
        g.user.group_chat_styles = style_filter
        g.user.group_chat_levels = level_filter

    groups_query = g.db.query(GroupChat).filter(and_(
        GroupChat.publicity.in_(("listed", "pinned")),
        GroupChat.style.in_(style_filter),
        GroupChat.level.in_(level_filter),
    )).all()

    pipeline = g.redis.pipeline()
    for group in groups_query:
        pipeline.hvals("chat:%s:online" % group.id)

    groups = []
    for group, online_users in zip(groups_query, pipeline.execute()):
        online_user_count = len(set(online_users))
        if online_user_count > 0:
            groups.append((group, online_user_count))
    groups.sort(key=lambda _: (_[0].publicity, _[1]), reverse=True)

    chat_dicts = []
    for chat, online in groups:
        cd = chat.to_dict()
        cd["online"] = online
        chat_dicts.append(cd)

    if fmt == "json":
        return jsonify({
            "chats": chat_dicts,
        })

    return render_template(
        "groups.html",
        groups=chat_dicts,
        style_filter=style_filter,
        level_filter=level_filter,
    )


@use_db
def health():
    g.redis.set("health", 1)
    g.db.query(SearchCharacter).first()
    return "ok"


@use_db
@admin_required
def api_users():
    if not request.args.get("email_address"):
        abort(404)
    return jsonify({
        "users": [
            {"id": user.id, "username": user.username} for user in
            g.db.query(User).filter(and_(
                func.lower(User.email_address) == request.args["email_address"].strip().lower()[:100],
                User.email_verified == True,
            ))
        ]
    })


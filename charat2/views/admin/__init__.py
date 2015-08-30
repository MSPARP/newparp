import json
import paginate
import time

from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers import alt_formats
from charat2.helpers.auth import admin_required
from charat2.model import AdminLogEntry, GroupChat, SearchCharacter, SearchCharacterChoice, User
from charat2.model.connections import use_db
from charat2.model.validators import color_validator


@use_db
@admin_required
def home():
    return render_template("admin/home.html")


@use_db
@admin_required
def announcements_get():
    return render_template("admin/announcements.html")


@use_db
@admin_required
def announcements_post():
    if "announcements" in request.form:
        current_announcements = g.redis.get("announcements")
        if request.form["announcements"] != current_announcements:
            g.redis.set("announcements", request.form["announcements"])
            g.db.add(AdminLogEntry(
                action_user=g.user,
                type="announcements",
                description=request.form["announcements"],
            ))
    if "chat_links" in request.form:
        current_chat_links = g.redis.get("chat_links")
        if request.form["chat_links"] != current_chat_links:
            g.redis.set("chat_links", request.form["chat_links"])
            g.db.add(AdminLogEntry(
                action_user=g.user,
                type="chat_links",
                description=request.form["chat_links"],
            ))
    return redirect(url_for("admin_announcements"))


@use_db
@admin_required
def broadcast_get():
    return render_template("admin/broadcast.html")


@use_db
@admin_required
def broadcast_post():

    text = request.form["text"].strip()
    if not text:
        abort(400)

    if request.form["color"][0] == "#":
        color = request.form["color"][1:]
    else:
        color = request.form["color"]
    if not color_validator.match(color):
        abort(400)

    g.db.add(AdminLogEntry(
        action_user=g.user,
        type="broadcast",
        description=text,
    ))

    message_json = json.dumps({
        "messages": [{
            "id": None,
            "user_number": None,
            "posted": time.time(),
            "type": "global",
            "color": color,
            "acronym": "",
            "name": "",
            "text": text,
        }]
    })

    next_index = 0
    while True:
        next_index, keys = g.redis.scan(next_index,"chat:*:online")
        for key in keys:
            chat_id = key[5:-7]
            g.redis.publish("channel:%s" % chat_id, message_json)
        if int(next_index) == 0:
            break

    return redirect(url_for("admin_broadcast"))


def _filter_users(query):

    if "group" in request.args:
        user_group = request.args["group"].strip().lower()
        if user_group not in User.group.type.enums:
            abort(404)
        query = query.filter(User.group == user_group)

    if request.args.get("username"):
        query = query.filter(func.lower(User.username).like("%" + request.args["username"].strip().lower() + "%"))

    return query


@alt_formats({"json"})
@use_db
@admin_required
def user_list(fmt=None, page=1):

    users = g.db.query(User)
    users = _filter_users(users)
    users = users.order_by(User.id).offset((page - 1) * 50).limit(50).all()

    if len(users) == 0 and page != 1:
        abort(404)

    user_count = g.db.query(func.count('*')).select_from(User)
    user_count = _filter_users(user_count)
    user_count = user_count.scalar()

    if fmt == "json":
        return jsonify({
            "total": user_count,
            "users": [_.to_dict(include_options=True) for _ in users],
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=user_count,
        url_maker=lambda page: url_for("admin_user_list", page=page, **request.args),
    )
    group_link_args = request.args.copy()
    if "group" in group_link_args:
        del group_link_args["group"]
    return render_template(
        "admin/user_list.html",
        User=User,
        users=users,
        paginator=paginator,
        group_link_args=group_link_args,
    )


@alt_formats({"json"})
@use_db
@admin_required
def user(username, fmt=None):
    try:
        user = (
            g.db.query(User).filter(func.lower(User.username) == username.lower())
            .options(
                joinedload(User.default_character),
                joinedload(User.roulette_search_character),
                joinedload(User.search_character),
            ).one()
        )
    except NoResultFound:
        abort(404)
    # Redirect to fix capitalisation.
    if username != user.username:
        return redirect(url_for("admin_user", username=user.username))
    if fmt == "json":
        return jsonify(user.to_dict(include_options=True))
    search_characters = ", ".join(_.title for _ in (
        g.db.query(SearchCharacter)
        .select_from(SearchCharacterChoice)
        .join(SearchCharacter)
        .filter(SearchCharacterChoice.user_id == user.id)
        .order_by(SearchCharacter.name).all()
    ))
    return render_template("admin/user.html", User=User, user=user, search_characters=search_characters)


@use_db
@admin_required
def user_set_group(username):
    if request.form["group"] not in User.group.type.enums:
        abort(400)
    try:
        user = g.db.query(User).filter(func.lower(User.username) == username.lower()).one()
    except NoResultFound:
        abort(404)
    if user.group != request.form["group"]:
        user.group = request.form["group"]
        g.db.add(AdminLogEntry(
            action_user=g.user,
            type="user_set_group",
            description=request.form["group"],
            affected_user=user,
        ))
    return redirect(url_for("admin_user", username=user.username))


@alt_formats({"json"})
@use_db
@admin_required
def groups(fmt=None, page=1):
    groups = (
        g.db.query(GroupChat)
        .order_by(GroupChat.id)
        .options(joinedload(GroupChat.creator))
        .offset((page - 1) * 50).limit(50).all()
    )
    if len(groups) == 0 and page != 1:
        abort(404)
    group_count = g.db.query(func.count('*')).select_from(GroupChat).scalar()
    if fmt == "json":
        group_dicts = []
        for group in groups:
            group_dict = group.to_dict()
            group_dict["creator"] = group.creator.to_dict()
            group_dicts.append(group_dict)
        return jsonify({
            "total": group_count,
            "groups": group_dicts,
        })
    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=group_count,
        url_maker=lambda page: url_for("admin_groups", page=page),
    )
    return render_template(
        "admin/groups.html",
        groups=groups,
        paginator=paginator,
    )


@alt_formats({"json"})
@use_db
@admin_required
def log(fmt=None, page=1):

    if "type" in request.args:
        entry_type = request.args["type"].strip().lower()
    else:
        entry_type = None

    entries = g.db.query(AdminLogEntry)
    if entry_type == "spamless":
        entries = entries.filter(AdminLogEntry.type.like("spamless:%"))
    elif entry_type is not None:
        entries = entries.filter(AdminLogEntry.type == entry_type)
    entries = entries.order_by(
        AdminLogEntry.id.desc(),
    ).options(
        joinedload(AdminLogEntry.action_user),
        joinedload(AdminLogEntry.affected_user),
        joinedload(AdminLogEntry.chat),
    ).offset((page - 1) * 50).limit(50).all()

    if len(entries) == 0 and page != 1:
        abort(404)
    entry_count = g.db.query(func.count('*')).select_from(AdminLogEntry)
    if entry_type is not None:
        entry_count = entry_count.filter(AdminLogEntry.type == entry_type)
    entry_count = entry_count.scalar()
    if fmt == "json":
        return jsonify({
            "total": entry_count,
            "entries": [_.to_dict() for _ in entries],
        })
    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=entry_count,
        url_maker=lambda page: url_for("admin_log", page=page, type=entry_type),
    )
    return render_template(
        "admin/log.html",
        entries=entries,
        paginator=paginator,
    )


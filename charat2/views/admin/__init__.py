import json
import paginate
import time

from collections import OrderedDict, namedtuple
from flask import abort, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func
from sqlalchemy.exc import DataError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers import alt_formats
from charat2.helpers.auth import admin_required
from charat2.model import AdminLogEntry, GroupChat, IPBan, SearchCharacter, SearchCharacterChoice, User
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

    if request.args.get("ip"):
        # XXX VALIDATE THIS
        query = query.filter(User.last_ip.op("<<=")(request.args["ip"]))

    return query


user_order = namedtuple("user_order", ("name", "column"))
user_orders = OrderedDict([
    ("id", user_order("#", User.id)),
    ("username", user_order("Username", func.lower(User.username))),
    ("group", user_order("Group", User.group)),
    ("created", user_order("Created", User.created.desc())),
    ("last_online", user_order("Last online", User.last_online.desc())),
    ("last_ip", user_order("Last IP", User.last_ip)),
    ("timezone", user_order("Time zone", User.timezone)),
])


@alt_formats({"json"})
@use_db
@admin_required
def user_list(fmt=None, page=1):

    users = g.db.query(User)
    users = _filter_users(users)

    if request.args.get("order") in user_orders:
        users = users.order_by(user_orders[request.args["order"]].column)
    else:
        users = users.order_by(user_orders["id"].column)

    try:
        users = users.offset((page - 1) * 50).limit(50).all()
    except DataError:
        abort(400)

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
        user_orders=user_orders,
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
    ip_bans = (
        g.db.query(IPBan)
        .filter(IPBan.address.op(">>=")(user.last_ip))
        .order_by(IPBan.address).all()
    )
    if fmt == "json":
        user = user.to_dict(include_options=True)
        user["ip_bans"] = [_.to_dict() for _ in ip_bans]
        return jsonify(user)
    search_characters = ", ".join(_.title for _ in (
        g.db.query(SearchCharacter)
        .select_from(SearchCharacterChoice)
        .join(SearchCharacter)
        .filter(SearchCharacterChoice.user_id == user.id)
        .order_by(SearchCharacter.name).all()
    ))
    return render_template(
        "admin/user.html",
        User=User,
        user=user,
        ip_bans=[_.address for _ in ip_bans],
        search_characters=search_characters,
    )


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


@alt_formats({"json"})
@use_db
@admin_required
def ip_bans(fmt=None, page=1):

    ip_bans = (
        g.db.query(IPBan)
        .options(joinedload(IPBan.creator))
        .order_by(IPBan.address)
        .offset((page - 1) * 50).limit(50).all()
    )

    if page != 1 and len(ip_bans) == 0:
        abort(404)

    ip_ban_count = g.db.query(func.count('*')).select_from(IPBan).scalar()

    if fmt == "json":
        return jsonify({
            "total": ip_ban_count,
            "ip_bans": [_.to_dict() for _ in ip_bans],
        })

    paginator = paginate.Page(
        [],
        page=page,
        items_per_page=50,
        item_count=ip_ban_count,
        url_maker=lambda page: url_for("admin_ip_bans", page=page),
    )

    return render_template(
        "admin/ip_bans.html",
        ip_bans=ip_bans,
        paginator=paginator,
    )


@use_db
@admin_required
def new_ip_ban():

    if not request.form.get("reason"):
        abort(400)

    if "subnet" in request.form:
        full_address = request.form["address"] + "/" + request.form["subnet"]
    else:
        full_address = request.form["address"]

    try:
        existing_ban = (
            g.db.query(func.count('*')).select_from(IPBan)
            .filter(IPBan.address == full_address).scalar()
        )
    except DataError:
        abort(400)

    if existing_ban != 0:
        return redirect(url_for("admin_ip_bans", ip_ban_error="already_banned"))

    try:
        g.db.add(IPBan(
            address = full_address[:42],
            creator_id = g.user.id,
            reason = request.form["reason"][:255],
        ))
        g.db.flush()
    except DataError:
        abort(400)

    g.db.add(AdminLogEntry(
        action_user=g.user,
        type="ip_ban",
        description="Banned %s. Reason: %s" % (full_address, request.form["reason"]),
    ))

    if request.headers.get("Referer"):
        referer = request.headers["Referer"]
        if "?ip_ban_error=already_banned" in referer:
            referer = referer.replace("?ip_ban_error=already_banned", "")
        return redirect(referer)

    return redirect(url_for("admin_ip_bans"))


@use_db
@admin_required
def delete_ip_ban():
    try:
        g.db.query(IPBan).filter(IPBan.address == request.form["address"]).delete()
    except DataError:
        abort(400)
    g.db.add(AdminLogEntry(
        action_user=g.user,
        type="ip_ban",
        description="Unbanned %s." % request.form["address"],
    ))
    return redirect(request.headers.get("Referer") or url_for("admin_ip_bans"))


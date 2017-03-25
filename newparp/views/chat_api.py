import json
import time

from flask import abort, g, jsonify, make_response, redirect, request, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from newparp.helpers.characters import validate_character_form
from newparp.helpers.chat import (
    group_chat_only,
    require_socket,
    send_message,
    send_temporary_message,
    send_userlist,
    disconnect,
    disconnect_user,
    send_quit_message,
    get_userlist,
)
from newparp.model import (
    case_options,
    level_options,
    Ban,
    Block,
    Character,
    ChatUser,
    GroupChat,
    Invite,
    Message,
    User,
)
from newparp.model.connections import (
    get_chat_user,
    use_db_chat,
    db_connect,
    db_commit,
    db_disconnect,
)
from newparp.model.validators import color_validator


@use_db_chat
@require_socket
def send():

    if g.chat_user.computed_group == "silent":
        abort(403)

    if "text" not in request.form:
        abort(400)

    text = request.form["text"].strip()[:Message.MAX_LENGTH]

    if text == "":
        abort(400)

    message_type = request.form.get("type", "ic")
    if message_type not in ("ic", "ooc", "me"):
        message_type = "ic"

    # Set color, name and acronym based on a saved character.
    character = None
    if "character_id" in request.form:
        try:
            character = g.db.query(Character).filter(and_(
                Character.id == request.form["character_id"],
                Character.user_id == g.user.id,
            )).order_by(Character.title).one()
        except NoResultFound:
            pass

    send_message(g.db, g.redis, Message(
        chat_id=g.chat.id,
        user_id=g.user.id,
        type=message_type,
        color=character.color if character is not None else g.chat_user.color,
        acronym=character.acronym if character is not None else g.chat_user.acronym,
        name=character.name if character is not None else g.chat_user.name,
        text=text,
    ))

    # Clear typing status so the front end doesn't have to.
    if g.redis.scard("chat:%s:sockets:%s" % (g.chat.id, g.session_id)):
        typing_key = "chat:%s:typing" % g.chat.id
        if g.redis.srem(typing_key, g.chat_user.number):
            g.redis.publish("channel:%s:typing" % g.chat.id, json.dumps({
                "typing": list(int(_) for _ in g.redis.smembers(typing_key)),
            }))

    g.chat_user.draft = ""

    return "", 204


@use_db_chat
@require_socket
def draft():
    g.chat_user.draft = request.form.get("text", "").strip()[:Message.MAX_LENGTH]
    return "", 204


@use_db_chat
@require_socket
def block():

    if g.chat.type not in ("roulette", "searched"):
        abort(404)

    # Fetch the ChatUser we're trying to block.
    try:
        blocked_chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.chat_id == g.chat.id,
            ChatUser.user_id != g.user.id,
            ChatUser.number == int(request.form["number"]),
        )).one()
    except (ValueError, NoResultFound):
        abort(404)

    reason = request.form.get("reason", "").strip()[:500]

    # Skip without doing anything if they're already blocked.
    if g.db.query(func.count("*")).select_from(Block).filter(and_(
        Block.blocking_user_id == g.user.id,
        Block.blocked_user_id == blocked_chat_user.user_id,
    )).scalar() == 0:
        g.db.add(Block(
            blocking_user_id=g.user.id,
            blocked_user_id=blocked_chat_user.user_id,
            chat_id=g.chat.id,
            reason=reason if reason else None,
        ))

    return "", 204


@require_socket
def set_state():
    raise NotImplementedError


@use_db_chat
@group_chat_only
def set_group():

    # Admins and creators can do this from the chat users list, so only require
    # a socket if we're not one.
    if (
        g.redis.scard("chat:%s:sockets:%s" % (g.chat.id, g.session_id)) == 0
        and not (g.user.is_admin or g.user.id == g.chat.creator_id)
    ):
        abort(403)

    # Validation #1: We must be allowed to set groups.
    if not g.chat_user.can("set_group"):
        abort(403)

    # Validation #2: Set group must be lower than ours.
    # Also 400 if the group is invalid.
    set_group = request.form["group"]
    try:
        if ChatUser.group_ranks[set_group] >= g.chat_user.computed_rank:
            abort(403)
    except KeyError:
        abort(400)

    # Fetch the ChatUser we're trying to change.
    try:
        set_chat_user, set_user = g.db.query(ChatUser, User).join(
            User, ChatUser.user_id == User.id,
        ).filter(and_(
            ChatUser.chat_id == g.chat.id,
            ChatUser.number == int(request.form["number"]),
        )).one()
    except (ValueError, NoResultFound):
        abort(404)

    # Validation #3: Set user's group must be lower than ours.
    if set_chat_user.computed_rank >= g.chat_user.computed_rank:
        abort(403)

    # If we're changing them to their current group, just send a 204 without
    # actually doing anything.
    if set_group == set_chat_user.group:
        return "", 204

    if set_group == "mod3":
        message = ("%s [%s] set %s [%s] to Professional Wet Blanket. They can now silence, kick and ban other users.")
    elif set_group == "mod2":
        message = ("%s [%s] set %s [%s] to Bum's Rusher. They can now silence and kick other users.")
    elif set_group == "mod1":
        message = ("%s [%s] set %s [%s] to Amateur Gavel-Slinger. They can now silence other users.")
    elif set_group == "user":
        if set_chat_user.group == "silent":
            message = ("%s [%s] unsilenced %s [%s].")
        else:
            message = ("%s [%s] removed moderator status from %s [%s].")
    elif set_group == "silent":
        message = ("%s [%s] silenced %s [%s].")

    set_chat_user.group = set_group

    send_message(g.db, g.redis, Message(
        chat_id=g.chat.id,
        user_id=set_chat_user.user_id,
        name=set_chat_user.name,
        type="user_group",
        text=message % (
            g.chat_user.name, g.chat_user.acronym,
            set_chat_user.name, set_chat_user.acronym,
        ),
    ))

    return "", 204


@use_db_chat
@require_socket
@group_chat_only
def user_action():

    action = request.form["action"]
    if action not in ("kick", "ban"):
        abort(400)

    # Validation #1: We must be allowed to perform this action.
    if not g.chat_user.can(action):
        abort(403)

    # Fetch the ChatUser we're trying to act upon.
    try:
        set_chat_user, set_user = g.db.query(ChatUser, User).join(
            User, ChatUser.user_id == User.id,
        ).filter(and_(
            ChatUser.chat_id == g.chat.id,
            ChatUser.number == int(request.form["number"]),
        )).one()
    except (ValueError, NoResultFound):
        abort(404)

    # Validation #2: Set user's group must be lower than ours.
    if set_chat_user.computed_rank >= g.chat_user.computed_rank:
        abort(403)

    if action == "kick":
        g.redis.publish(
            "channel:%s:%s" % (g.chat.id, set_user.id),
            "{\"exit\":\"kick\"}",
        )
        # Don't allow them back in for 30 seconds.
        kick_key = "kicked:%s:%s" % (g.chat.id, set_user.id)
        g.redis.set(kick_key, 1)
        g.redis.expire(kick_key, 30)
        # Only send a kick message if they're currently online.
        if disconnect_user(g.redis, g.chat.id, set_user.id):
            send_message(g.db, g.redis, Message(
                chat_id=g.chat.id,
                user_id=set_user.id,
                type="user_action",
                name=g.chat_user.name,
                text=(
                    "%s [%s] kicked %s [%s] from the chat."
                ) % (
                    g.chat_user.name, g.chat_user.acronym,
                    set_chat_user.name, set_chat_user.acronym,
                )
            ))
        return "", 204

    elif action == "ban":
        # In private chats, this un-invites someone instead of banning them.
        if g.chat.publicity == "private":
            deleted = g.db.query(Invite).filter(and_(
                Invite.chat_id == g.chat.id,
                Invite.user_id == set_user.id,
            )).delete()
            # Don't send a message if there wasn't an invite.
            if not deleted:
                return "", 204
            ban_message = (
                "%s [%s] un-invited %s [%s] from the chat."
            ) % (
                g.chat_user.name, g.chat_user.acronym,
                set_chat_user.name, set_chat_user.acronym,
            )
        else:
            # Skip if they're already banned.
            if g.db.query(func.count('*')).select_from(Ban).filter(and_(
                Ban.chat_id == g.chat.id,
                Ban.user_id == set_user.id,
            )).scalar() != 0:
                return "", 204
            reason = None
            if "reason" in request.form:
                reason = request.form["reason"].strip()[:500] or None
            g.db.add(Ban(
                user_id=set_user.id,
                chat_id=g.chat.id,
                creator_id=g.user.id,
                reason=reason,
            ))
            if request.form.get("reason") is not None:
                ban_message = (
                    "%s [%s] banned %s [%s] from the chat. Reason: %s"
                ) % (
                    g.chat_user.name, g.chat_user.acronym,
                    set_chat_user.name, set_chat_user.acronym,
                    reason,
                )
            else:
                ban_message = (
                    "%s [%s] banned %s [%s] from the chat."
                ) % (
                    g.chat_user.name, g.chat_user.acronym,
                    set_chat_user.name, set_chat_user.acronym,
                )
        g.redis.publish(
            "channel:%s:%s" % (g.chat.id, set_user.id),
            "{\"exit\":\"ban\"}",
        )
        disconnect_user(g.redis, g.chat.id, set_user.id)
        send_message(g.db, g.redis, Message(
            chat_id=g.chat.id,
            user_id=set_user.id,
            type="user_action",
            name=g.chat_user.name,
            text=ban_message,
        ))
        # Unsubscribe if necessary.
        set_chat_user.subscribed = False
        return "", 204


@use_db_chat
@require_socket
@group_chat_only
def set_flag():

    flag = request.form["flag"]
    value = request.form["value"]
    if "flag" not in request.form or "value" not in request.form:
        abort(400)

    # Validation: We must be allowed to set flags.
    if not g.chat_user.can("set_flag"):
        abort(403)

    # Boolean flags.
    if (flag in ("autosilence") and value in ("on", "off")):
        new_value = value == "on"
        if new_value == getattr(g.chat, flag):
            return "", 204
        setattr(g.chat, flag, new_value)
        message = ("%%s [%%s] switched %s %s.") % (flag, value)

    elif (flag == "style" and value in ("script", "paragraph", "either")):
        if value == g.chat.style:
            return "", 204
        g.chat.style = value
        if g.chat.style == "script":
            message = "%s [%s] marked the chat as script style."
        elif g.chat.style == "paragraph":
            message = "%s [%s] marked the chat as paragraph style."
        elif g.chat.style == "either":
            message = "%s [%s] marked the chat as either style."

    elif (flag == "level" and value in level_options):
        if value == g.chat.level:
            return "", 204
        g.chat.level = value
        if g.chat.level == "sfw":
            message = "%s [%s] marked the chat as safe for work."
        elif g.chat.level == "nsfws":
            message = "%s [%s] marked the chat as not safe for work due to sexual content."
        elif g.chat.level == "nsfwv":
            message = "%s [%s] marked the chat as not safe for work due to violent content."
        elif g.chat.level == "nsfw-extreme":
            message = "%s [%s] marked the chat as NSFW extreme."

    # Publicity is also an enum because we might add options for password
    # protected or invite only chats in the future.
    elif (flag == "publicity" and value in GroupChat.publicity.type.enums):
        # Only admins can set/unset pinned and admin_only.
        admin_values = ("pinned", "admin_only")
        if (value in admin_values or g.chat.publicity in admin_values) and g.chat_user.computed_group != "admin":
            abort(403)
        if value == g.chat.publicity:
            return "", 204
        g.chat.publicity = value
        if g.chat.publicity == "private":
            message = "%s [%s] set the chat to private. Only users who have been invited can enter."
        elif g.chat.publicity == "unlisted":
            message = "%s [%s] unlisted the chat. Anyone can visit this chat, but only if they have the URL."
        elif g.chat.publicity == "listed":
            message = "%s [%s] listed the chat. It's now listed on the public chats page."
        elif g.chat.publicity == "pinned":
            message = "%s [%s] pinned the chat. It's now listed at the top of the public chats page."
        elif g.chat.publicity == "admin_only":
            message = "%s [%s] restricted the chat to admins."

    else:
        abort(400)

    send_message(g.db, g.redis, Message(
        chat_id=g.chat.id,
        user_id=g.user.id,
        type="chat_meta",
        text=message % (g.chat_user.name, g.chat_user.acronym),
    ))

    return "", 204


@use_db_chat
@require_socket
@group_chat_only
def set_topic():

    # Validation: We must be allowed to set the topic.
    if not g.chat_user.can("set_topic"):
        abort(403)

    topic = request.form["topic"].strip()[:500]
    # If it hasn't changed, don't bother sending a message about it.
    if topic == g.chat.topic:
        return "", 204
    g.chat.topic = topic

    if topic == "":
        send_message(g.db, g.redis, Message(
            chat_id=g.chat.id,
            user_id=g.user.id,
            name=g.chat_user.name,
            type="chat_meta",
            text="%s [%s] removed the conversation topic." % (
                g.chat_user.name, g.chat_user.acronym,
            ),
        ))
    else:
        send_message(g.db, g.redis, Message(
            chat_id=g.chat.id,
            user_id=g.user.id,
            name=g.chat_user.name,
            type="chat_meta",
            text="%s [%s] changed the topic to \"%s\"" % (
                g.chat_user.name, g.chat_user.acronym, topic,
            ),
        ))

    return "", 204


@use_db_chat
@require_socket
@group_chat_only
def set_info():

    # Validation: We must be allowed to set the topic.
    if not g.chat_user.can("set_info"):
        abort(403)

    description = request.form["description"].strip()[:Message.MAX_LENGTH]
    rules = request.form["rules"].strip()[:Message.MAX_LENGTH]
    # If it hasn't changed, don't bother sending a message about it.
    if (description == g.chat.description and rules == g.chat.rules):
        return "", 204
    g.chat.description = description
    g.chat.rules = rules

    send_message(g.db, g.redis, Message(
        chat_id=g.chat.id,
        user_id=g.user.id,
        name=g.chat_user.name,
        type="chat_meta",
        text="%s [%s] edited the chat information." % (
            g.chat_user.name, g.chat_user.acronym,
        ),
    ))

    return "", 204


@use_db_chat
@require_socket
def save():

    # Remember old values so we can check if they've changed later.
    old_name = g.chat_user.name
    old_acronym = g.chat_user.acronym
    old_color = g.chat_user.color

    new_details = validate_character_form(request.form)
    g.chat_user.search_character_id = new_details["search_character_id"]
    g.chat_user.name = new_details["name"]
    g.chat_user.acronym = new_details["acronym"]
    g.chat_user.color = new_details["color"]
    g.chat_user.quirk_prefix = new_details["quirk_prefix"]
    g.chat_user.quirk_suffix = new_details["quirk_suffix"]
    g.chat_user.case = new_details["case"]
    g.chat_user.replacements = new_details["replacements"]
    g.chat_user.regexes = new_details["regexes"]

    # Send a message if name or acronym has changed.
    if g.chat_user.name != old_name or g.chat_user.acronym != old_acronym:
        if g.chat_user.computed_group == "silent":
            send_userlist(g.db, g.redis, g.chat)
        else:
            send_message(g.db, g.redis, Message(
                chat_id=g.chat.id,
                user_id=g.user.id,
                type="user_info",
                name=g.chat_user.name,
                text=("%s [%s] is now %s [%s].") % (
                    old_name, old_acronym,
                    g.chat_user.name, g.chat_user.acronym,
                ),
            ))
    # Just refresh the user list if the color has changed.
    elif g.chat_user.color != old_color:
        send_userlist(g.db, g.redis, g.chat)

    return jsonify(g.chat_user.to_dict(include_options=True))


@use_db_chat
@require_socket
def save_from_character():

    try:
        character = g.db.query(Character).filter(and_(
            Character.id == request.form["character_id"],
            Character.user_id == g.user.id,
        )).order_by(Character.title).one()
    except NoResultFound:
        abort(404)

    old_color = g.chat_user.color

    # Send a message if name, acronym or color has changed.
    changed = (
        g.chat_user.name != character.name
        or g.chat_user.acronym != character.acronym
        or g.chat_user.color != character.color
    )

    g.chat_user.name = character.name
    g.chat_user.acronym = character.acronym
    g.chat_user.color = character.color
    g.chat_user.quirk_prefix = character.quirk_prefix
    g.chat_user.quirk_suffix = character.quirk_suffix
    g.chat_user.case = character.case
    g.chat_user.replacements = character.replacements
    g.chat_user.regexes = character.regexes

    if changed:
        if g.chat_user.computed_group == "silent":
            send_userlist(g.db, g.redis, g.chat)
        else:
            send_message(g.db, g.redis, Message(
                chat_id=g.chat.id,
                user_id=g.user.id,
                type="user_info",
                name=g.chat_user.name,
                text=("%s [%s] is now %s [%s].") % (
                    old_name, old_acronym,
                    g.chat_user.name, g.chat_user.acronym,
                ),
            ))

    return jsonify(g.chat_user.to_dict(include_options=True))


@use_db_chat
def save_variables():

    # Boolean variables.
    for variable in [
        "confirm_disconnect",
        "desktop_notifications",
        "show_system_messages",
        "show_user_numbers",
        "show_bbcode",
        "show_timestamps",
        "show_preview",
        "typing_notifications",
        "enable_activity_indicator",
    ]:
        if variable not in request.form:
            continue
        if request.form[variable] not in {"on", "off"}:
            abort(400)
        setattr(g.chat_user, variable, request.form[variable] == "on")

    for variable in [
        "highlighted_numbers",
        "ignored_numbers",
    ]:
        if variable not in request.form:
            continue
        # Convert to a set to remove duplicates.
        temp_set = set()
        for item in request.form[variable].split(","):
            try:
                temp_set.add(int(item.strip()))
            except ValueError:
                pass
        # XXX LENGTH LIMIT?
        setattr(g.chat_user, variable, list(temp_set))

    if request.headers.get("X-Requested-With") != "XMLHttpRequest" and "Referer" in request.headers:
        return redirect(request.headers["Referer"])

    return "", 204


@use_db_chat
@require_socket
def request_username():

    try:
        chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.chat_id == g.chat.id,
            ChatUser.number == int(request.form["number"]),
        )).one()
    except (ValueError, NoResultFound):
        abort(404)

    # This is pointless.
    if chat_user == g.chat_user:
        abort(400)

    # Don't allow another request for a minute.
    request_key = "request_username:%s:%s:%s" % (g.chat.id, g.user.id, chat_user.user_id)
    if g.redis.exists(request_key):
        return "", 204
    g.redis.setex(request_key, 60, "1")

    # Allow requests to be accepted for an hour.
    g.redis.setex("exchange_usernames:%s:%s:%s" % (g.chat.id, chat_user.user_id, g.user.id), 3600, "1")

    send_temporary_message(
        g.redis, g.chat, chat_user.user_id, g.chat_user.number, "username_request",
        "%s would like to exchange usernames." % g.chat_user.name,
    )

    return "", 204


@use_db_chat
@require_socket
def exchange_usernames():

    try:
        chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.chat_id == g.chat.id,
            ChatUser.number == int(request.form["number"]),
        )).options(joinedload(ChatUser.user)).one()
    except (ValueError, NoResultFound):
        abort(404)

    exchange_key = "exchange_usernames:%s:%s:%s" % (g.chat.id, g.user.id, chat_user.user_id)
    if not g.redis.exists(exchange_key):
        send_temporary_message(
            g.redis, g.chat, g.user.id, None, "username",
            "This request has expired. Please try again later.",
        )
        return "", 204

    send_temporary_message(
        g.redis, g.chat, chat_user.user_id, g.chat_user.number, "username",
        "%s is #%s %s. [url=%s]Private message[/url]" % (
            g.chat_user.name,
            g.user.id,
            g.user.username,
            url_for("rp_chat", url="pm/" + g.user.username, _external=True),
        ),
    )

    send_temporary_message(
        g.redis, g.chat, g.user.id, chat_user.number, "username",
        "%s is #%s %s. [url=%s]Private message[/url]" % (
            chat_user.name,
            chat_user.user.id,
            chat_user.user.username,
            url_for("rp_chat", url="pm/" + chat_user.user.username, _external=True),
        ),
    )

    g.redis.delete(exchange_key)

    return "", 204


@use_db_chat
@require_socket
def look_up_user():
    if not g.user.is_admin:
        abort(403)
    try:
        chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.chat_id == g.chat.id,
            ChatUser.number == int(request.form["number"]),
        )).options(joinedload(ChatUser.user)).one()
    except (ValueError, NoResultFound):
        abort(404)
    send_temporary_message(
        g.redis, g.chat, g.user.id, None, "chat_meta",
        "User number %s is [url=%s]#%s %s[/url], last IP [url=%s]%s[/url]. ([url=%s]F[/url])" % (
            chat_user.number,
            url_for("admin_user", username=chat_user.user.username, _external=True),
            chat_user.user.id,
            chat_user.user.username,
            url_for("admin_user_list", ip=chat_user.user.last_ip, _external=True),
            chat_user.user.last_ip,
            "http://forums.msparp.com/modcp.php?action=ipsearch&ipaddress=" + chat_user.user.last_ip + "&search_users=1&search_posts=1",
        ),
    )
    return "", 204


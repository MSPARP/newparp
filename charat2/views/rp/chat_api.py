import json
import time

from flask import abort, g, jsonify, make_response, redirect, request, url_for
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.characters import validate_character_form
from charat2.helpers.chat import (
    group_chat_only,
    mark_alive,
    send_message,
    send_userlist,
    disconnect,
    disconnect_user,
    send_quit_message,
    get_userlist,
)
from charat2.model import (
    case_options,
    Ban,
    GroupChat,
    ChatUser,
    Message,
    User,
    Character,
)
from charat2.model.connections import (
    get_chat_user,
    use_db_chat,
    db_connect,
    db_commit,
    db_disconnect,
)
from charat2.model.validators import color_validator


@mark_alive
def messages():

    try:
        after = int(request.form["after"])
    except (KeyError, ValueError):
        after = 0

    # Look for stored messages first, and only subscribe if there aren't any.
    messages = g.redis.zrangebyscore("chat:%s" % g.chat_id, "(%s" % after, "+inf")

    if "joining" in request.form or g.joining:
        db_connect()
        get_chat_user()
        return jsonify({
            "users": get_userlist(g.db, g.redis, g.chat),
            "chat": g.chat.to_dict(),
            "messages": [json.loads(_) for _ in messages],
        })
    elif len(messages) != 0:
        message_dict = { "messages": [json.loads(_) for _ in messages] }
        return jsonify(message_dict)

    pubsub = g.redis.pubsub()
    # Channel for general chat messages.
    pubsub.subscribe("channel:%s" % g.chat_id)
    # Channel for messages aimed specifically at you - kicks, bans etc.
    pubsub.subscribe("channel:%s:%s" % (g.chat_id, g.user_id))

    # Get rid of the database connection here so we're not hanging onto it
    # while waiting for the redis message.
    db_commit()
    db_disconnect()

    for msg in pubsub.listen():
        if msg["type"] == "message":
            # The pubsub channel sends us a JSON string, so we return that
            # instead of using jsonify.
            resp = make_response(msg["data"])
            resp.headers["Content-type"] = "application/json"
            return resp


@mark_alive
def ping():
    return "", 204


@use_db_chat
@mark_alive
def send():

    if (
        g.chat_user.group == "silent"
        and g.chat.creator != g.user
        and g.user.group != "admin"
    ):
        abort(403)

    if "text" not in request.form:
        abort(400)

    # Change double spaces to no-break space.
    text = request.form["text"].strip().replace("  ", u" \u00A0")[:5000]
    if text == "":
        abort(400)

    message_type = request.form.get("type", "ic")

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

    return "", 204


@mark_alive
def set_state():
    raise NotImplementedError


@use_db_chat
@group_chat_only
@mark_alive
def set_group():

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

    if set_group == "mod":
        message = ("%s [%s] set %s [%s] to Professional Wet Blanket. They can now silence, kick and ban other users.")
    elif set_group == "mod2":
        message = ("%s [%s] set %s [%s] to Bum's Rusher. They can now silence and kick other users.")
    elif set_group == "mod3":
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
@group_chat_only
@mark_alive
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
        return "", 204


@use_db_chat
@group_chat_only
@mark_alive
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

    elif (flag == "level" and value in ("sfw", "nsfw", "nsfw-extreme")):
        if value == g.chat.level:
            return "", 204
        g.chat.level = value
        if g.chat.level == "sfw":
            message = "%s [%s] marked the chat as safe for work."
        elif g.chat.level == "nsfw":
            message = "%s [%s] marked the chat as not safe for work."
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
        if g.chat.publicity == "unlisted":
            message = "%s [%s] unlisted the chat."
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
@group_chat_only
@mark_alive
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
@group_chat_only
@mark_alive
def set_info():

    # Validation: We must be allowed to set the topic.
    if not g.chat_user.can("set_info"):
        abort(403)

    description = request.form["description"].strip()[:5000]
    rules = request.form["rules"].strip()[:5000]
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
@mark_alive
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
        if g.chat_user.group == "silent":
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
@mark_alive
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
        if g.chat_user.group == "silent":
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
        "show_bbcode",
        "show_preview",
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
@mark_alive
def look_up_user():
    if g.user.group != "admin":
        abort(403)
    try:
        chat_user = g.db.query(ChatUser).filter(and_(
            ChatUser.chat_id == g.chat.id,
            ChatUser.number == int(request.form["number"]),
        )).options(joinedload(ChatUser.user)).one()
    except (ValueError, NoResultFound):
        abort(404)
    g.redis.publish("channel:%s:%s" % (g.chat.id, g.user.id), json.dumps({"messages": [{
        "id": None,
        "user_number": None,
        "posted": time.time(),
        "type": "chat_meta",
        "color": "000000",
        "acronym": "",
        "name": "",
        "text": "User number %s is [url=%s]#%s %s[/url], last IP %s." % (
            chat_user.number,
            url_for("admin_user", username=chat_user.user.username, _external=True),
            chat_user.user.id,
            chat_user.user.username,
            chat_user.user.last_ip,
        ),
    }]}))
    return "", 204


def quit():
    # Only send a message if we were already online.
    if g.user_id is None or "chat_id" not in request.form:
        abort(400)
    try:
        g.chat_id = int(request.form["chat_id"])
    except ValueError:
        abort(400)
    if disconnect(g.redis, g.chat_id, g.session_id):
        db_connect()
        get_chat_user()
        send_quit_message(g.db, g.redis, g.chat_user, g.user, g.chat)
    return "", 204


import json

from flask import abort, g, jsonify, make_response, request
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.chat import (
    group_chat_only,
    mark_alive,
    send_message,
    send_userlist,
    disconnect,
    get_userlist,
)
from charat2.model import (
    case_options,
    Ban,
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

    if "joining" in request.form or g.joining:
        db_connect()
        get_chat_user()
        return jsonify({
            "users": get_userlist(g.db, g.redis, g.chat),
            "chat": g.chat.to_dict(),
        })

    # Look for stored messages first, and only subscribe if there aren't any.
    messages = g.redis.zrangebyscore("chat:%s" % g.chat_id, "(%s" % after, "+inf")
    if len(messages) != 0 or g.joining:
        message_dict = { "messages": [json.loads(_) for _ in messages] }
        return jsonify(message_dict)

    pubsub = g.redis.pubsub()
    # Channel for general chat messages.
    pubsub.subscribe("channel:%s" % g.chat_id)
    # Channel for messages aimed specifically at you - kicks, bans etc.
    pubsub.subscribe("channel:%s:%s" % (g.chat_id, g.user_id))

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
    text = request.form["text"].replace("  ", u" \u00A0")
    if text == "":
        abort(400)

    message_type = request.form.get("type", "ic")

    send_message(g.db, g.redis, Message(
        chat_id=g.chat.id,
        user_id=g.user.id,
        type=message_type,
        color=g.chat_user.color,
        alias=g.chat_user.alias,
        name=g.chat_user.name,
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
    if "user_id" in request.form:
        user_condition = ChatUser.user_id == request.form["user_id"]
    elif "username" in request.form:
        user_condition = func.lower(User.username) == request.form["username"].lower()
    else:
        abort(400)
    try:
        set_chat_user, set_user = g.db.query(ChatUser, User).join(
            User, ChatUser.user_id == User.id,
        ).filter(and_(
            user_condition,
            ChatUser.chat_id == g.chat.id,
        )).one()
    except NoResultFound:
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
            g.chat_user.name, g.chat_user.alias,
            set_chat_user.name, set_chat_user.alias,
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
    if "user_id" in request.form:
        user_condition = ChatUser.user_id == request.form["user_id"]
    elif "username" in request.form:
        user_condition = func.lower(User.username) == request.form["username"].lower()
    else:
        abort(400)
    try:
        set_chat_user, set_user = g.db.query(ChatUser, User).join(
            User, ChatUser.user_id == User.id,
        ).filter(and_(
            user_condition,
            ChatUser.chat_id == g.chat.id,
        )).one()
    except NoResultFound:
        abort(404)

    # Validation #2: Set user's group must be lower than ours.
    if set_chat_user.computed_rank >= g.chat_user.computed_rank:
        abort(403)

    if action == "kick":
        g.redis.publish(
            "channel:%s:%s" % (g.chat.id, set_user.id),
            "{\"exit\":\"kick\"}",
        )
        # Don't allow them back in for 10 seconds.
        kick_key = "kicked:%s:%s" % (g.chat.id, set_user.id)
        g.redis.set(kick_key, 1)
        g.redis.expire(kick_key, 10)
        disconnect(g.redis, g.chat.id, set_user.id)
        send_message(g.db, g.redis, Message(
            chat_id=g.chat.id,
            user_id=set_user.id,
            type="user_action",
            name=g.chat_user.name,
            text=(
                "%s [%s] kicked %s [%s] from the chat."
            ) % (
                g.chat_user.name, g.chat_user.alias,
                set_chat_user.name, set_chat_user.alias,
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
        g.db.add(Ban(
            user_id=set_user.id,
            chat_id=g.chat.id,
            creator_id=g.user.id,
            name=set_chat_user.name,
            alias=set_chat_user.alias,
            reason=request.form.get("reason"),
        ))
        if request.form.get("reason") is not None:
            ban_message = (
                "%s [%s] banned %s [%s] from the chat. Reason: %s"
            ) % (
                g.chat_user.name, g.chat_user.alias,
                set_chat_user.name, set_chat_user.alias,
                request.form["reason"],
            )
        else:
            ban_message = (
                "%s [%s] banned %s [%s] from the chat."
            ) % (
                g.chat_user.name, g.chat_user.alias,
                set_chat_user.name, set_chat_user.alias,
            )
        g.redis.publish(
            "channel:%s:%s" % (g.chat.id, set_user.id),
            "{\"exit\":\"ban\"}",
        )
        disconnect(g.redis, g.chat.id, set_user.id)
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
    if (flag in ("autosilence", "nsfw") and value in ("on", "off")):
        new_value = value == "on"
        if new_value == getattr(g.chat, flag):
            return "", 204
        setattr(g.chat, flag, new_value)
        message = ("%%s [%%s] switched %s %s.") % (flag, value)

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
    elif (flag == "publicity" and value in ("listed", "unlisted")):
        if value == g.chat.publicity:
            return "", 204
        g.chat.publicity = value
        if g.chat.publicity == "listed":
            message = "%s [%s] listed the chat. It's now listed on the public rooms page."
        elif g.chat.publicity == "unlisted":
            message = "%s [%s] unlisted the chat."

    else:
        abort(400)

    send_message(g.db, g.redis, Message(
        chat_id=g.chat.id,
        user_id=g.user.id,
        type="chat_meta",
        text=message % (g.chat_user.name, g.chat_user.alias),
    ))

    return "", 204


@use_db_chat
@group_chat_only
@mark_alive
def set_topic():

    # Validation: We must be allowed to set the topic.
    if not g.chat_user.can("set_topic"):
        abort(403)

    if "topic" not in request.form:
        abort(400)

    topic = request.form["topic"].strip()

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
                g.chat_user.name, g.chat_user.alias,
            ),
        ))
    else:
        send_message(g.db, g.redis, Message(
            chat_id=g.chat.id,
            user_id=g.user.id,
            name=g.chat_user.name,
            type="chat_meta",
            text="%s [%s] changed the topic to \"%s\"" % (
                g.chat_user.name, g.chat_user.alias, topic,
            ),
        ))

    return "", 204


@use_db_chat
@mark_alive
def save():

    # Remember old values so we can check if they've changed later.
    old_name = g.chat_user.name
    old_alias = g.chat_user.alias
    old_color = g.chat_user.color

    # Don't allow a blank name.
    if request.form["name"] == "":
        abort(400)

    # Validate color.
    if not color_validator.match(request.form["color"]):
        abort(400)
    g.chat_user.color = request.form["color"]

    # Validate case.
    if request.form["case"] not in case_options:
        abort(400)
    g.chat_user.case = request.form["case"]

    # There are length limits on the front end so just silently truncate these.
    g.chat_user.name = request.form["name"][:50]
    g.chat_user.alias = request.form["alias"][:15]
    g.chat_user.quirk_prefix = request.form["quirk_prefix"][:50]
    g.chat_user.quirk_suffix = request.form["quirk_suffix"][:50]

    # XXX PUT LENGTH LIMIT ON REPLACEMENTS?
    # Zip replacements.
    replacements = zip(
        request.form.getlist("quirk_from"),
        request.form.getlist("quirk_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    replacements = [_ for _ in replacements if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    g.chat_user.replacements = json.dumps(replacements)

    # XXX PUT LENGTH LIMIT ON REGEXES?
    # Zip regexes.
    regexes = zip(
        request.form.getlist("regex_from"),
        request.form.getlist("regex_to"),
    )
    # Strip out any rows where from is blank or the same as to.
    regexes = [_ for _ in regexes if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    g.chat_user.regexes = json.dumps(regexes)

    # Send a message if name or alias has changed.
    if (
        g.chat_user.name != old_name
        or g.chat_user.alias != old_alias
        or g.chat_user.color != old_color
    ):
        if g.chat_user.group == "silent":
            send_userlist(g.db, g.redis, g.chat)
        else:
            send_message(g.db, g.redis, Message(
                chat_id=g.chat.id,
                user_id=g.user.id,
                type="user_info",
                name=g.chat_user.name,
                text=("%s [%s] is now %s [%s].") % (
                    old_name, old_alias,
                    g.chat_user.name, g.chat_user.alias,
                ),
            ))

    return "", 204


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

    # Send a message if name, alias or color has changed.
    changed = (
        g.chat_user.name != character.name
        or g.chat_user.alias != character.alias
        or g.chat_user.color != character.color
    )

    g.chat_user.name = character.name
    g.chat_user.alias = character.alias
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
                    old_name, old_alias,
                    g.chat_user.name, g.chat_user.alias,
                ),
            ))

    return "", 204


@use_db_chat
@mark_alive
def save_variables():

    # Boolean variables.
    for variable in [
        "confirm_disconnect",
        "desktop_notifications",
        "show_description",
        "show_connection_messages",
        "show_ic_messages",
        "show_ooc_messages",
        "show_message_info",
        "show_bbcode",
        "show_preview",
        "ooc_on",
    ]:
        if variable not in request.form:
            continue
        if request.form[variable] not in {"on", "off"}:
            abort(400)
        setattr(g.chat_user, variable, request.form[variable] == "on")

    for variable in [
        "highlighted_user_ids",
        "blocked_user_ids",
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

    return "", 204


def quit():
    # Only send a message if we were already online.
    if g.user_id is None or "chat_id" not in request.form:
        abort(400)
    try:
        g.chat_id = int(request.form["chat_id"])
    except ValueError:
        abort(400)
    if disconnect(g.redis, g.chat_id, g.user_id):
        db_connect()
        get_chat_user()
        if g.chat_user.group == "silent":
            send_userlist(g.db, g.redis, g.chat)
        else:
            send_message(g.db, g.redis, Message(
                chat_id=g.chat.id,
                user_id=g.user.id,
                type="disconnect",
                name=g.chat_user.name,
                text=("%s [%s] disconnected.") % (
                    g.chat_user.name, g.chat_user.alias,
                ),
            ))
    return "", 204


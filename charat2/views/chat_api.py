import json

from flask import abort, g, jsonify, make_response, request
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.chat import (
    mark_alive,
    send_message,
    send_userlist,
    disconnect,
    get_userlist,
)
from charat2.model import (
    action_ranks,
    case_options,
    group_ranks,
    Ban,
    Message,
    UserChat,
)
from charat2.model.connections import (
    get_user_chat,
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
    if len(messages) != 0 or g.joining:
        message_dict = { "messages": [json.loads(_) for _ in messages] }
        if g.joining:
            message_dict["users"] = get_userlist(g.db, g.redis, g.chat)
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
        if msg["type"]=="message":
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

    if g.user_chat.group == "silent":
        abort(403)

    if "text" not in request.form:
        abort(400)

    text = request.form["text"].strip()
    if text == "":
        abort(400)

    message_type = "ic"
    # Automatic OOC detection
    if (
        text.startswith("((") or text.endswith("))")
        or text.startswith("[[") or text.endswith("]]")
        or text.startswith("{{") or text.endswith("}}")
    ):
        message_type="ooc"

    send_message(g.db, g.redis, Message(
        chat_id=g.chat.id,
        user_id=g.user.id,
        type=message_type,
        color=g.user_chat.color,
        acronym=g.user_chat.acronym,
        text=text,
    ))

    return "", 204

@mark_alive
def set_state():
    raise NotImplementedError

@use_db_chat
@mark_alive
def set_group():

    # Only allow mods to be set in group chats.
    if g.chat.type!="group":
        abort(400)

    # Validate group setting.
    if request.form.get("group") not in group_ranks:
        abort(400)

    # If we're not a mod, creator or site admin, don't even bother looking up
    # the other user.
    if (
        group_ranks[g.user_chat.group] == 0
        and g.chat.creator != g.user
        and g.user.group != "admin"
    ):
        abort(403)

    # Fetch the UserChat we're trying to change.
    try:
        set_user_chat = g.db.query(UserChat).filter(and_(
            UserChat.user_id==request.form["user_id"],
            UserChat.chat_id==g.chat.id,
        )).options(joinedload(UserChat.user)).one()
    except NoResultFound:
        abort(404)

    # If they're the creator or a site admin, don't allow the change.
    if set_user_chat.user==g.chat.creator or set_user_chat.user.group=="admin":
        abort(403)

    # Creator and admin can do anything, so only do the following checks if
    # we're not.
    if g.chat.creator != g.user and g.user.group != "admin":
        # If the other user's group is above our own, don't allow the change.
        if group_ranks[set_user_chat.group] > group_ranks[g.user_chat.group]:
            abort(403)
        # If the group we're trying to set them to is above our own, don't allow
        # the change.
        if group_ranks[request.form["group"]] > group_ranks[g.user_chat.group]:
            abort(403)

    # If we're changing them to their current group, just send a 204 without
    # actually doing anything.
    if request.form["group"] == set_user_chat.group:
        return "", 204

    if request.form["group"] == "mod":
        message = ("%s set %s to Magical Mod. They can now silence, kick and "
                   "ban other users.")
    elif request.form["group"] == "mod2":
        message = ("%s set %s to Cute-Cute Mod. They can now silence and kick "
                   "other users.")
    elif request.form["group"] == "mod3":
        message = ("%s set %s to Little Mod. They can now silence other users.")
    elif request.form["group"] == "user":
        if set_user_chat.group == "silent":
            message = ("%s unsilenced %s.")
        else:
            message = ("%s removed moderator status from %s.")
    elif request.form["group"] == "silent":
        message = ("%s silenced %s.")

    set_user_chat.group = request.form["group"]

    send_message(g.db, g.redis, Message(
        chat_id=g.chat.id,
        type="user_group",
        text=message % (
            g.user_chat.name,
            set_user_chat.name
        ),
    ))

    return "", 204

@use_db_chat
@mark_alive
def user_action():

    if request.form.get("action") not in ("kick", "ban"):
        abort(400)

    # Make sure we're allowed to perform this action.
    if (
        group_ranks[g.user_chat.group] < action_ranks[request.form["action"]]
        and g.chat.creator != g.user
        and g.user.group != "admin"
    ):
        abort(403)

    # Fetch the UserChat we're trying to act upon.
    try:
        set_user_chat = g.db.query(UserChat).filter(and_(
            UserChat.user_id==request.form["user_id"],
            UserChat.chat_id==g.chat.id,
        )).options(joinedload(UserChat.user)).one()
    except NoResultFound:
        abort(404)

    # If they're above us, creator or admin, don't allow the action.
    if (
        group_ranks[set_user_chat.group] > group_ranks[g.user_chat.group]
        or set_user_chat.user==g.chat.creator
        or set_user_chat.user.group=="admin"
    ):
        abort(403)

    if request.form["action"]=="kick":
        g.redis.publish(
            "channel:%s:%s" % (g.chat.id, set_user_chat.user_id),
            "{\"exit\":\"kick\"}",
        )
        # Don't allow them back in for 10 seconds.
        kick_key = "kicked:%s:%s" % (g.chat.id, set_user_chat.user_id)
        g.redis.set(kick_key, 1)
        g.redis.expire(kick_key, 10)
        disconnect(g.redis, g.chat.id, set_user_chat.user_id)
        send_message(g.db, g.redis, Message(
            chat_id=g.chat.id,
            type="user_action",
            text="%s [%s] kicked %s [%s] from the chat." % (
                g.user_chat.name, g.user_chat.acronym,
                set_user_chat.name, set_user_chat.acronym,
            ),
        ))
        return "", 204

    elif request.form["action"]=="ban":
        # Skip if they're already banned.
        if g.db.query(func.count('*')).select_from(Ban).filter(and_(
            Ban.chat_id==g.chat.id,
            Ban.user_id==set_user_chat.user_id,
        )).scalar() != 0:
            return "", 204
        g.db.add(Ban(
            user_id=set_user_chat.user_id,
            chat_id=g.chat.id,
            name=set_user_chat.name,
            acronym=set_user_chat.acronym,
            reason=request.form.get("reason"),
        ))
        if request.form.get("reason") is not None:
            ban_message = "%s [%s] banned %s [%s] from the chat. Reason: %s" % (
                g.user_chat.name, g.user_chat.acronym,
                set_user_chat.name, set_user_chat.acronym,
                request.form["reason"],
            )
        else:
            ban_message = "%s [%s] banned %s [%s] from the chat." % (
                g.user_chat.name, g.user_chat.acronym,
                set_user_chat.name, set_user_chat.acronym,
            )
        g.redis.publish(
            "channel:%s:%s" % (g.chat.id, set_user_chat.user_id),
            "{\"exit\":\"ban\"}",
        )
        disconnect(g.redis, g.chat.id, set_user_chat.user_id)
        send_message(g.db, g.redis, Message(
            chat_id=g.chat.id,
            type="user_action",
            text=ban_message,
        ))
        return "", 204

@mark_alive
def set_flag():
    raise NotImplementedError

@mark_alive
def set_info():
    raise NotImplementedError

@use_db_chat
@mark_alive
def save():

    # Remember old values so we can check if they've changed later.
    old_name = g.user_chat.name
    old_acronym = g.user_chat.acronym
    old_color = g.user_chat.color

    # Don't allow a blank name.
    if request.form["name"] == "":
        abort(400)

    # Validate color.
    if not color_validator.match(request.form["color"]):
        abort(400)
    g.user_chat.color = request.form["color"]

    # Validate case.
    if request.form["case"] not in case_options:
        abort(400)
    g.user_chat.case = request.form["case"]

    # There are length limits on the front end so just silently truncate these.
    g.user_chat.name = request.form["name"][:50]
    g.user_chat.acronym = request.form["acronym"][:15]
    g.user_chat.quirk_prefix = request.form["quirk_prefix"][:50]
    g.user_chat.quirk_suffix = request.form["quirk_suffix"][:50]

    # XXX PUT LENGTH LIMIT ON REPLACEMENTS?
    # Zip replacements.
    replacements = zip(
        request.form.getlist("quirk_from"),
        request.form.getlist("quirk_to")
    )
    # Strip out any rows where from is blank or the same as to.
    replacements = [_ for _ in replacements if _[0] != "" and _[0] != _[1]]
    # And encode as JSON.
    g.user_chat.replacements = json.dumps(replacements)

    # Send a message if name or acronym has changed.
    if g.user_chat.name != old_name or g.user_chat.acronym != old_acronym:
        if g.user_chat.group == "silent":
            send_userlist(g.db, g.redis, g.chat)
        else:
            send_message(g.db, g.redis, Message(
                chat_id=g.chat.id,
                type="user_info",
                text="%s [%s] is now %s [%s]." % (
                    old_name, old_acronym,
                    g.user_chat.name, g.user_chat.acronym,
                ),
            ))

    return "", 204

def quit():
    # Only send the message if we were already online.
    if g.user_id is None or "chat_id" not in request.form:
        abort(400)
    try:
        g.chat_id = int(request.form["chat_id"])
    except ValueError:
        abort(400)
    if disconnect(g.redis, g.chat_id, g.user_id):
        db_connect()
        get_user_chat()
        if g.user_chat.group == "silent":
            send_userlist(g.db, g.redis, g.chat)
        else:
            send_message(g.db, g.redis, Message(
                chat_id=g.chat.id,
                type="disconnect",
                text="%s [%s] disconnected." % (
                    g.user_chat.name, g.user_chat.acronym,
                ),
            ))
    return "", 204


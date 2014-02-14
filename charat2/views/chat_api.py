from flask import g, jsonify, make_response, request

from charat2.auth import user_chat_required
from charat2.model import Message

@user_chat_required
def messages():
    # Look for messages in the database first, and only subscribe if there
    # aren't any.
    message_query = g.db.query(Message).filter(Message.chat_id == g.chat.id)
    if "after" in request.form:
        after = int(request.form["after"])
        message_query = message_query.filter(Message.id > after)
    # Order descending to limit it to the last 50 messages.
    message_query = message_query.order_by(Message.id.desc()).limit(50)
    messages = message_query.all()
    if len(messages) != 0:
        messages.reverse()
        return jsonify({
            "messages": [_.to_dict() for _ in messages],
        })
    pubsub = g.redis.pubsub()
    # Channel for general chat messages.
    pubsub.subscribe("channel.%s" % g.chat.id)
    # Channel for messages aimed specifically at you - kicks, bans etc.
    pubsub.subscribe("channel.%s.%s" % (g.chat.id, g.user.id))
    for msg in pubsub.listen():
        if msg["type"]=="message":
            # The pubsub channel sends us a JSON string, so we return that
            # instead of using jsonify.
            resp = make_response(msg["data"])
            resp.headers["Content-type"] = "application/json"
            return resp

@user_chat_required
def send():
    raise NotImplementedError

@user_chat_required
def set_state():
    raise NotImplementedError

@user_chat_required
def set_group():
    raise NotImplementedError

@user_chat_required
def user_action():
    raise NotImplementedError

@user_chat_required
def set_flag():
    raise NotImplementedError

@user_chat_required
def set_topic():
    raise NotImplementedError

@user_chat_required
def save():
    raise NotImplementedError

@user_chat_required
def ping():
    raise NotImplementedError

@user_chat_required
def quit():
    raise NotImplementedError


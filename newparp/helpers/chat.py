import json
import time

from flask import abort, g
from functools import wraps
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload

from newparp.model import AgeGroup, allowed_level_options, Ban, Invite, ChatUser, Message
from newparp.model.connections import NewparpRedis, redis_chat_pool
from newparp.model.user_list import UserListStore
from newparp.tasks import celery


class UnauthorizedException(Exception):
    pass


class BannedException(Exception):
    pass


class BadAgeException(Exception):
    pass


class TooManyPeopleException(Exception):
    pass


class KickedException(Exception):
    pass


def require_socket(f):
    """Only allow this request if the user has a socket open."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user_list.session_has_open_socket(g.session_id, g.user.id):
            print("doesn't have open socket")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def group_chat_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.chat.type != "group":
            abort(404)
        return f(*args, **kwargs)
    return decorated_function


def authorize_joining(db, context):
    """Stuff to be verified before a person can join a chat.

    This includes checking whether they're banned, whether the chat is private,
    and whether there are already too many people in the chat.

    These checks are run before a socket is opened, so the kick check can't
    happen here because it needs to send a message back to the client rather
    than just 403ing.
    """

    # Admins bypass all restrictions.
    if context.user is not None and context.user.is_admin:
        return

    if context.chat.type == "group":

        if context.chat.publicity == "admin_only":
            raise UnauthorizedException

        if context.chat.publicity == "private":

            if context.user is None:
                raise UnauthorizedException

            # Creators bypass all restrictions in their chats
            if context.user_id == context.chat.creator_id:
                return

            if db.query(func.count('*')).select_from(Invite).filter(and_(
                Invite.chat_id == context.chat_id,
                Invite.user_id == context.user_id,
            )).scalar() != 1:
                raise UnauthorizedException

    if db.query(func.count('*')).select_from(Ban).filter(and_(
        Ban.chat_id == context.chat_id,
        Ban.user_id == context.user_id,
    )).scalar() != 0:
        raise BannedException

    if context.chat.type == "group":
        if context.user is None and context.chat.level not in allowed_level_options[AgeGroup.unknown]:
            raise BadAgeException
        elif context.user is not None and context.chat.level not in context.user.level_options:
            raise BadAgeException

    online_user_count = len(context.user_list.user_ids_online())
    if online_user_count >= 50:
        raise TooManyPeopleException


def kick_check(redis, context):
    # If they've been kicked recently, don't let them in.
    if redis.exists("kicked:%s:%s" % (context.chat.id, context.user.id)):
        raise KickedException


def send_join_message(user_list, db, redis, context):
    """
    Send join message or delete previous disconnect message:
    * If the last message in the chat was a disconnect from this user, it's
      deleted.
    * If not, a join message is sent.
    * Either way, the user list is refreshed.
    """

    # Queue their last_online update.
    redis.hset("queue:usermeta", "chatuser:%s" % context.chat_user.user_id, json.dumps({
        "last_online": str(time.time()),
        "chat_id": context.chat_user.chat_id,
    }))

    if context.chat_user.computed_group == "silent" or context.chat.type in ("pm", "roulette"):
        send_userlist(user_list, db, context.chat)
    else:
        last_message = db.query(Message).filter(Message.chat_id == context.chat.id).order_by(Message.posted.desc()).first()
        # If they just disconnected, delete the disconnect message instead.
        if last_message is not None and last_message.type in ("disconnect", "timeout") and last_message.user_id == context.user.id:
            delete_message(user_list, db, last_message, force_userlist=True)
        else:
            send_message(db, user_list.redis, Message(
                chat_id=context.chat.id,
                user_id=context.user.id,
                type="join",
                name=context.chat_user.name,
                text="%s [%s] joined chat. %s" % (
                    context.chat_user.name,
                    context.chat_user.acronym,
                    "~~MxRP STAFF~~" if context.user.is_admin else ""
                ),
            ), user_list)


def send_message(db, redis, message, user_list=None, force_userlist=False):

    db.add(message)
    db.flush()

    message_dict = message.to_dict()

    # Cache before sending.
    cache_key = "chat:%s" % message.chat_id
    redis.zadd(cache_key, message.id, json.dumps(message_dict))
    redis.zremrangebyrank(cache_key, 0, -51)
    redis.expire(cache_key, 604800)

    # Prepare pubsub message
    redis_message = {
        "messages": [message_dict],
    }

    # Reload userlist if necessary.
    if message.type in (
        "join",
        "disconnect",
        "timeout",
        "user_info",
        "user_group",
        "user_action",
    ) or force_userlist:
        if user_list is None:
            user_list = UserListStore(NewparpRedis(connection_pool=redis_chat_pool), message.chat_id)
        redis_message["users"] = get_userlist(user_list, db)

    # Reload chat metadata if necessary.
    if message.type == "chat_meta":
        redis_message["chat"] = message.chat.to_dict()

    redis.publish("channel:%s" % message.chat_id, json.dumps(redis_message))

    # Send notifications.
    if message.type in ("ic", "ooc", "me", "spamless"):

        # Queue an update for the last_online field.
        # TODO move the PM stuff here too
        redis.hset("queue:lastonline", message.chat.id, time.mktime(message.posted.timetuple()) + float(message.posted.microsecond) / 1000000)

        if user_list is None:
            user_list = UserListStore(NewparpRedis(connection_pool=redis_chat_pool), message.chat_id)
        online_user_ids = user_list.user_ids_online()
        if message.chat.type == "pm":
            offline_chat_users = db.query(ChatUser).filter(and_(
                ~ChatUser.user_id.in_(online_user_ids),
                ChatUser.chat_id == message.chat.id,
            ))
            for chat_user in offline_chat_users:
                # Only send a notification if it's not already unread.
                if message.chat.last_message <= chat_user.last_online:
                    redis.publish("channel:pm:%s" % chat_user.user_id, "{\"pm\":\"1\"}")

    # And send the message to spamless last.
    # 1 second delay to prevent the task from executing before we commit the message.
    celery.send_task("newparp.tasks.spamless.CheckSpamTask", args=(message.chat_id, redis_message), countdown=1)


def send_temporary_message(redis, chat, to_id, user_number, message_type, text):
    redis.publish("channel:%s:%s" % (chat.id, to_id), json.dumps({"messages": [{
        "id": None,
        "user_number": user_number,
        "posted": time.time(),
        "type": message_type,
        "color": "000000",
        "acronym": "",
        "name": "",
        "text": text
    }]}))


def delete_message(user_list, db, message, force_userlist=False):
    redis_message = {"delete": [message.id]}
    if force_userlist:
        redis_message["users"] = get_userlist(user_list, db)
    user_list.redis.publish("channel:%s" % message.chat_id, json.dumps(redis_message))
    user_list.redis.zremrangebyscore("chat:%s" % message.chat_id, message.id, message.id)
    db.delete(message)


def get_userlist(user_list, db):
    online_user_ids = user_list.user_ids_online()
    # Don't bother querying if the list is empty.
    # Also set the message cache to expire.
    if len(online_user_ids) == 0:
        user_list.redis.expire("chat:%s" % user_list.chat_id, 30)
        return []
    return [
        _.to_dict() for _ in
        db.query(ChatUser).filter(and_(
            ChatUser.user_id.in_(online_user_ids),
            ChatUser.chat_id == user_list.chat_id,
        )).order_by(ChatUser.name).options(joinedload(ChatUser.user))
    ]


def send_userlist(user_list, db, chat):
    # Update the userlist without sending a message.
    if chat.type == "pm":
        for user_id, in db.query(ChatUser.user_id).filter(ChatUser.chat_id == user_list.chat_id):
            user_list.redis.publish("channel:pm:%s" % user_id, "{\"pm\":\"1\"}")
    user_list.redis.publish("channel:%s" % user_list.chat_id, json.dumps({
        "messages": [],
        "users": get_userlist(user_list, db),
    }))


def send_quit_message(user_list, db, chat_user, user, chat, type="disconnect"):
    if chat_user.computed_group == "silent" or chat.type in ("pm", "roulette"):
        send_userlist(user_list, db, chat)
    else:
        if type == "disconnect":
            text = "%s [%s] disconnected." % (chat_user.name, chat_user.acronym)
        elif type == "timeout":
            text = "%s's connection timed out." % chat_user.name
        send_message(db, user_list.redis, Message(
            chat_id=chat.id,
            user_id=user.id,
            type=type,
            name=chat_user.name,
            text=text,
        ), user_list)


#!/usr/bin/python

import datetime
import time
import json

from redis import StrictRedis
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.chat import disconnect, send_message, send_userlist
from charat2.model import sm, Message, Chat, ChatUser
from charat2.model.connections import redis_pool

if __name__ == "__main__":

    db = sm()

    print("Obtaining lock...")
    db.query(func.pg_advisory_lock(413, 1)).scalar()
    print("Lock obtained.")

    redis = StrictRedis(connection_pool=redis_pool)

    while True:

        current_time = int(time.time())

        # Make sure a message is sent every 25 seconds so the long poll requests
        # don't time out.
        # XXX INCREASE THIS TO SEVERAL MINUTES
        for chat_id in redis.zrangebyscore("longpoll_timeout", 0, current_time):
            redis.publish("channel:%s" % chat_id, "{\"messages\":[]}")
            if redis.hlen("chat:%s:online" % chat_id) != 0:
                redis.zadd("longpoll_timeout", time.time() + 25, chat_id)
            else:
                redis.zrem("longpoll_timeout", chat_id)

        # And do the reaping.
        disconnected_users = set()

        # Long poll sessions.
        for dead in redis.zrangebyscore("chats_alive", 0, current_time):
            print("Reaping %s" % dead)
            chat_id, session_id = dead.split('/')
            user_id = redis.hget("chat:%s:online" % chat_id, session_id)
            disconnected = disconnect(redis, chat_id, session_id)
            # Only send a timeout message if they were already online.
            if not disconnected:
                print("Not sending timeout message.")
                continue
            disconnected_users.add((chat_id, user_id, False))

        # Sockets.
        for dead in redis.zrangebyscore("sockets_alive", 0, current_time):
            print("Reaping %s" % dead)
            chat_id, session_id, socket_id = dead.split('/')
            user_id = redis.hget("chat:%s:online" % chat_id, socket_id)
            disconnected = disconnect(redis, chat_id, socket_id)
            redis.srem("chat:%s:sockets:%s" % (chat_id, session_id), socket_id)
            redis.zrem("sockets_alive", "%s/%s/%s" % (chat_id, session_id, socket_id))
            # Only send a timeout message if they were already online.
            if not disconnected:
                print("Not sending timeout message.")
                continue
            disconnected_users.add((chat_id, user_id, True))

        for chat_id, user_id, reaped_socket in disconnected_users:
            try:
                dead_chat_user = db.query(ChatUser).filter(and_(
                    ChatUser.user_id == user_id,
                    ChatUser.chat_id == chat_id,
                )).options(joinedload(ChatUser.chat), joinedload(ChatUser.user)).one()
            except NoResultFound:
                print("Unable to find ChatUser (chat %s, user %s)." % (chat_id, user_id))
                continue

            if reaped_socket:
                typing_key = "chat:%s:typing" % chat_id
                if redis.srem(typing_key, dead_chat_user.number):
                    redis.publish("channel:%s:typing" % chat_id, json.dumps({
                        "typing": list(int(_) for _ in redis.smembers(typing_key)),
                    }))

            if dead_chat_user.computed_group == "silent" or dead_chat_user.chat.type in ("pm", "roulette"):
                send_userlist(db, redis, dead_chat_user.chat)
            else:
                send_message(db, redis, Message(
                    chat_id=chat_id,
                    user_id=dead_chat_user.user_id,
                    type="timeout",
                    name=dead_chat_user.name,
                    text="%s's connection timed out." % dead_chat_user.name,
                ))
            print("Sent timeout message for ChatUser (chat %s, user %s)." % (chat_id, user_id))

        db.commit()

        # Generate connected/searching counters every 10 seconds.
        if int(current_time) % 10 == 0:

            print("Generating user counters.")
            connected_users = set()
            next_index = 0
            while True:
                next_index, keys = redis.scan(next_index, "chat:*:online")
                for key in keys:
                    for user_id in redis.hvals(key):
                        connected_users.add(user_id)
                if int(next_index) == 0:
                    break
            redis.set("connected_users", len(connected_users))
            searching_users = set()
            for searcher_id in redis.smembers("searchers"):
                session_id = redis.get("searcher:%s:session_id" % searcher_id)
                user_id = redis.get("session:%s" % session_id)
                if user_id is not None:
                    searching_users.add(user_id)
            redis.set("searching_users", len(searching_users))
            rouletting_users = set()
            for searcher_id in redis.smembers("roulette_searchers"):
                session_id = redis.get("roulette:%s:session_id" % searcher_id)
                user_id = redis.get("session:%s" % session_id)
                if user_id is not None:
                    rouletting_users.add(user_id)
            redis.set("rouletting_users", len(rouletting_users))

            # Updates the last_online fields here
            chat_ids = redis.hgetall("queue:lastonline")
            redis.delete("queue:lastonline")
            print("Updating last_online values: %s" % chat_ids)

            for chat_id, posted in chat_ids.iteritems():
                online_user_ids = set(int(_) for _ in redis.hvals("chat:%s:online" % chat_id))
                try:
                    posted = datetime.datetime.utcfromtimestamp(float(posted))
                except ValueError:
                    continue
                db.query(Chat).filter(Chat.id == chat_id).update({"last_message": posted}, synchronize_session=False)
                if len(online_user_ids) != 0:
                    db.query(ChatUser).filter(and_(
                        ChatUser.user_id.in_(online_user_ids),
                        ChatUser.chat_id == chat_id,
                    )).update({"last_online": posted}, synchronize_session=False)
                db.commit()

        time.sleep(1)

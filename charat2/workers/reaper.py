#!/usr/bin/python

import time

from redis import StrictRedis
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from charat2.helpers.chat import disconnect, send_message, send_userlist
from charat2.model import sm, Message, ChatUser
from charat2.model.connections import redis_pool

if __name__ == "__main__":
    db = sm()
    redis = StrictRedis(connection_pool=redis_pool)
    while True:

        current_time = int(time.time())

        # Make sure a message is sent every 25 seconds so the long poll requests
        # don't time out.
        # XXX INCREASE THIS TO SEVERAL MINUTES
        for chat_id in redis.zrangebyscore("longpoll_timeout", 0, current_time):
            redis.publish("channel:%s" % chat_id, "{\"messages\":[]}")
            if redis.scard("chat:%s:online" % chat_id) != 0:
                redis.zadd("longpoll_timeout", time.time() + 25, chat_id)
            else:
                redis.zrem("longpoll_timeout", chat_id)

        # And do the reaping.
        for dead in redis.zrangebyscore("chats_alive", 0, current_time):
            chat_id, user_id = dead.split('/')
            disconnected = disconnect(redis, chat_id, user_id)
            # Only send a timeout message if they were already online.
            if not disconnected:
                continue
            try:
                dead_chat_user = db.query(ChatUser).filter(and_(
                    ChatUser.user_id == user_id,
                    ChatUser.chat_id == chat_id,
                )).options(joinedload(ChatUser.chat), joinedload(ChatUser.user)).one()
            except NoResultFound:
                pass
            if dead_chat_user.group == "silent":
                send_userlist(db, redis, dead_chat_user.chat)
            else:
                send_message(db, redis, Message(
                    chat_id=chat_id,
                    user_id=dead_chat_user.user_id,
                    type="timeout",
                    name=dead_chat_user.name,
                    text="%s's connection timed out." % dead_chat_user.name,
                ))
            print current_time, "Reaping ", dead
        db.commit()

        # Generate connected/searching counters every 10 seconds.
        if int(current_time) % 10 == 0:
            connected_users = set()
            for chat_user in redis.zrange("chats_alive", 0, -1):
                chat_id, user_id = chat_user.split("/")
                connected_users.add(user_id)
            redis.set("connected_users", len(connected_users))
            searching_users = set()
            for searcher_id in redis.smembers("searchers"):
                session_id = redis.get("searcher:%s:session_id" % searcher_id)
                user_id = redis.get("session:%s" % session_id)
                if user_id is not None:
                    searching_users.add(user_id)
            for searcher_id in redis.smembers("roulette_searchers"):
                session_id = redis.get("roulette:%s:session_id" % searcher_id)
                user_id = redis.get("session:%s" % session_id)
                if user_id is not None:
                    searching_users.add(user_id)
            redis.set("searching_users", len(searching_users))

        time.sleep(1)


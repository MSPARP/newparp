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
        for dead in redis.zrangebyscore("chats_alive", 0, current_time):
            chat_id, user_id = dead.split('/')
            disconnected = disconnect(redis, chat_id, user_id)
            # Only send a timeout message if they were already online.
            if not disconnected:
                continue
            try:
                dead_chat_user = db.query(ChatUser).filter(and_(
                    ChatUser.user_id==user_id,
                    ChatUser.chat_id==chat_id,
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
                    text="[color=#%s]%s[/color] lost connection." % (
                        dead_chat_user.color, dead_chat_user.user.username,
                    ),
                ))
            print current_time, "Reaping ", dead
        db.commit()
        time.sleep(1)


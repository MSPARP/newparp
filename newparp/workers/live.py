#!/usr/bin/python


import json
import os
import re
import signal
import sys
import time

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from redis import StrictRedis
from sqlalchemy import and_, func
from sqlalchemy.orm.exc import NoResultFound
from tornado.gen import coroutine, Task
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from tornadoredis import Client
from uuid import uuid4

from newparp.helpers.chat import (
    UnauthorizedException,
    BannedException,
    TooManyPeopleException,
    KickedException,
    authorize_joining,
    kick_check,
    join,
    send_userlist,
    get_userlist,
    disconnect,
    send_quit_message,
)
from newparp.model import sm, AnyChat, Ban, ChatUser, Message, User, SearchCharacter
from newparp.model.connections import redis_pool

redis = StrictRedis(connection_pool=redis_pool)
thread_pool = ThreadPoolExecutor()


origin_regex = re.compile("^https?:\/\/%s$" % os.environ["BASE_DOMAIN"].replace(".", "\."))


sockets = set()

DEBUG = "DEBUG" in os.environ or "--debug" in sys.argv

class ChatHandler(WebSocketHandler):
    @property
    def db(self):
        if hasattr(self, "_db") and self._db is not None:
            return self._db
        else:
            self._db = sm()

    def get_chat_user(self):
        return self.db.query(
            ChatUser, User, AnyChat,
        ).join(
            User, ChatUser.user_id == User.id,
        ).join(
            AnyChat, ChatUser.chat_id == AnyChat.id,
        ).filter(and_(
            ChatUser.user_id == self.user_id,
            ChatUser.chat_id == self.chat_id,
        )).one()

    def set_typing(self, is_typing):
        command = redis.sadd if is_typing else redis.srem
        typing_key = "chat:%s:typing" % self.chat_id
        if command(typing_key, self.user_number):
            redis.publish(self.channels["typing"], json.dumps({
                "typing": list(int(_) for _ in redis.smembers(typing_key)),
            }))

    def safe_write(self, message):
        try:
            self.write_message(message)
        except WebSocketClosedError:
            return

    def check_origin(self, origin):
        return origin_regex.match(origin) is not None

    @coroutine
    def prepare(self):
        self.id = str(uuid4())
        self.joined = False
        try:
            self.session_id = self.cookies["newparp"].value
            self.chat_id = int(self.path_args[0])
            self.user_id = int(redis.get("session:%s" % self.session_id))
        except (KeyError, TypeError, ValueError):
            self.send_error(400)
            return
        try:
            self.chat_user, self.user, self.chat = yield thread_pool.submit(self.get_chat_user)
        except NoResultFound:
            self.send_error(404)
            return
        # Remember the user number so typing notifications can refer to it
        # without reopening the database session.
        self.user_number = self.chat_user.number
        self.user.last_online = datetime.now()
        self.user.last_ip = self.request.headers["X-Forwarded-For"]
        if self.user.group == "banned":
            self.send_error(403)
            return
        try:
            yield thread_pool.submit(authorize_joining, redis, self.db, self)
        except (UnauthorizedException, BannedException, TooManyPeopleException):
            self.send_error(403)
            return

    @coroutine
    def open(self, chat_id):

        redis.zadd("sockets_alive", time.time() + 60, "%s/%s/%s" % (self.chat_id, self.session_id, self.id))
        sockets.add(self)
        redis.sadd("chat:%s:sockets:%s" % (self.chat_id, self.session_id), self.id)
        if DEBUG:
            print("socket opened: %s %s %s" % (self.id, self.chat.url, self.user.username))

        try:
            kick_check(redis, self)
        except KickedException:
            self.safe_write(json.dumps({"exit": "kick"}))
            self.close()
            return

        # Subscribe
        self.channels = {
            "chat": "channel:%s" % self.chat_id,
            "user": "channel:%s:%s" % (self.chat_id, self.user_id),
            "typing": "channel:%s:typing" % self.chat_id,
        }
        if self.chat.type == "pm":
            self.channels["pm"] = "channel:pm:%s" % self.user_id
        yield self.redis_listen()

        # Send backlog.
        try:
            after = int(self.request.query_arguments["after"][0])
        except (KeyError, IndexError, ValueError):
            after = 0
        messages = redis.zrangebyscore("chat:%s" % self.chat_id, "(%s" % after, "+inf")
        self.safe_write(json.dumps({
            "chat": self.chat.to_dict(),
            "messages": [json.loads(_) for _ in messages],
        }))

        join_message_sent = yield thread_pool.submit(join, redis, self.db, self)
        self.joined = True

        # Send userlist if nothing was sent by join().
        if not join_message_sent:
            userlist = yield thread_pool.submit(get_userlist, self.db, redis, self.chat)
            self.safe_write(json.dumps({"users": userlist}))

        self.db.commit()
        self.db.close()

    def on_message(self, message):
        if redis.zadd("sockets_alive", time.time() + 60, "%s/%s/%s" % (self.chat_id, self.session_id, self.id)):
            # We've been reaped, so disconnect.
            self.close()
            return
        if DEBUG:
            print("message: %s" % message)
        if message in ("typing", "stopped_typing"):
            self.set_typing(message == "typing")

    def on_close(self):
        # Unsubscribe here and let the exit callback handle disconnecting.
        if hasattr(self, "redis_client"):
            self.redis_client.unsubscribe(self.redis_client.subscribed)
        if hasattr(self, "close_code") and self.close_code in (1000, 1001):
            message_type = "disconnect"
        else:
            message_type = "timeout"
        if self.joined and disconnect(redis, self.chat_id, self.id):
            try:
                send_quit_message(self.db, redis, *self.get_chat_user(), type=message_type)
            except NoResultFound:
                send_userlist(self.db, redis, self.chat)
            self.db.commit()
        # Delete the database connection here and on_finish just to be sure.
        if hasattr(self, "db"):
            self.db.close()
            self._db = None
        self.set_typing(False)
        if DEBUG:
            print("socket closed: %s" % (self.id))
        redis.srem("chat:%s:sockets:%s" % (self.chat_id, self.session_id), self.id)
        redis.zrem("sockets_alive", "%s/%s/%s" % (self.chat_id, self.session_id, self.id))

        try:
            sockets.remove(self)
        except KeyError:
            pass

    def on_finish(self):
        if hasattr(self, "db"):
            self.db.close()
            self._db = None

    @coroutine
    def redis_listen(self):
        self.redis_client = Client(
            host=os.environ["REDIS_HOST"],
            port=int(os.environ["REDIS_PORT"]),
            selected_db=int(os.environ["REDIS_DB"]),
        )
        # Set the connection name, subscribe, and listen.
        yield Task(self.redis_client.execute_command, "CLIENT", "SETNAME", "live:%s:%s" % (self.chat_id, self.user_id))
        yield Task(self.redis_client.subscribe, list(self.channels.values()))
        self.redis_client.listen(self.on_redis_message, self.on_redis_unsubscribe)

    def on_redis_message(self, message):
        if DEBUG:
            print("redis message: %s" % str(message))
        if message.kind != "message":
            return

        self.safe_write(message.body)

        if message.channel == self.channels["user"]:
            data = json.loads(message.body)
            if "exit" in data:
                self.joined = False
                self.close()

    def on_redis_unsubscribe(self, callback):
        self.redis_client.disconnect()


def sig_handler(sig, frame):
    print("Caught signal %s." % sig)
    ioloop.add_callback_from_signal(shutdown)


def shutdown():
    print("Shutting down.")
    for socket in sockets:
        ioloop.add_callback(socket.close)
    deadline = time.time() + 10

    def stop_loop():
        now = time.time()
        if now < deadline and (ioloop._callbacks or ioloop._timeouts):
            ioloop.add_timeout(now + 0.1, stop_loop)
        else:
            ioloop.stop()
    stop_loop()

class HealthHandler(RequestHandler):
    def prepare(self):
        self.db = sm()

    def get(self):
        redis.set("health", 1)
        self.db.query(SearchCharacter).first()
        self.write("ok")

    def on_finish(self):
        if hasattr(self, "db"):
            self.db.close()
            del self.db

if __name__ == "__main__":

    application = Application([
        (r"/(\d+)", ChatHandler),
        (r"/health", HealthHandler)
    ])

    http_server = HTTPServer(application)
    http_server.listen(int(os.environ.get("LISTEN_PORT", 5000)))

    ioloop = IOLoop.instance()
    ioloop.set_blocking_log_threshold(5.0)

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    ioloop.start()

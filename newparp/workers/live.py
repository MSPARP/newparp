#!/usr/bin/python


import asyncio
import json
import os
import re
import signal
import sys
import time
import functools

import asyncio_redis

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from sqlalchemy import and_, func
from sqlalchemy.orm.exc import NoResultFound
from tornado.gen import coroutine, Task
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from uuid import UUID, uuid4

from newparp.helpers.chat import (
    UnauthorizedException,
    BannedException,
    TooManyPeopleException,
    KickedException,
    authorize_joining,
    kick_check,
    send_join_message,
    send_userlist,
    send_quit_message,
)
from newparp.helpers.matchmaker import validate_searcher_exists, refresh_searcher
from newparp.helpers.users import queue_user_meta
from newparp.model import sm, AnyChat, Ban, ChatUser, Message, User, SearchCharacter
from newparp.model.connections import redis_pool, redis_chat_pool, NewparpRedis
from newparp.model.user_list import UserListStore, PingTimeoutException
from newparp.tasks.matchmaker import new_searcher


redis      = NewparpRedis(connection_pool=redis_pool)
redis_chat = NewparpRedis(connection_pool=redis_chat_pool)


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
            return self._db

    @property
    def loop(self):
        return asyncio.get_event_loop()

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
        if not hasattr(self, "channels") or not hasattr(self, "user_number"):
            return

        func = self.user_list.user_start_typing if is_typing else self.user_list.user_stop_typing
        if func(self.user_number):
            redis.publish(self.channels["typing"], json.dumps({
                "typing": self.user_list.user_numbers_typing(),
            }))

    def write_message(self, *args, **kwargs):
        try:
            super().write_message(*args, **kwargs)
        except WebSocketClosedError:
            return

    def check_origin(self, origin):
        if "localhost" in os.environ["BASE_DOMAIN"].lower():
            return True

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
        queue_user_meta(self, redis, self.request.headers.get("X-Forwarded-For", self.request.remote_ip))

        self.user_list = UserListStore(redis_chat, self.chat_id)

        try:
            if self.user.group != "active":
                raise BannedException

            yield thread_pool.submit(authorize_joining, redis, self.db, self)
        except (UnauthorizedException, BannedException, TooManyPeopleException):
            self.send_error(403)
            return

    @coroutine
    def open(self, chat_id):

        sockets.add(self)
        if DEBUG:
            print("socket opened: %s %s %s" % (self.id, self.chat.url, self.user.username))

        try:
            yield thread_pool.submit(kick_check, redis, self)
        except KickedException:
            self.write_message(json.dumps({"exit": "kick"}))
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

        self.redis_task = asyncio.ensure_future(self.redis_listen())

        # Send backlog.
        try:
            after = int(self.request.query_arguments["after"][0])
        except (KeyError, IndexError, ValueError):
            after = 0
        messages = redis.zrangebyscore("chat:%s" % self.chat_id, "(%s" % after, "+inf")
        self.write_message(json.dumps({
            "chat": self.chat.to_dict(),
            "messages": [json.loads(_) for _ in messages],
        }))

        online_state_changed = self.user_list.socket_join(self.id, self.session_id, self.user_id)
        self.joined = True

        # Send  a join message to everyone if we just joined, otherwise send the
        # user list to the client.
        if online_state_changed:
            yield thread_pool.submit(send_join_message, redis, self.db, self)
        else:
            userlist = yield thread_pool.submit(get_userlist, self.db, redis, self.chat)
            self.write_message(json.dumps({"users": userlist}))

        self.db.commit()
        self.db.close()

    def on_message(self, message):
        if DEBUG:
            print("message: %s" % message)
        if message == "ping":
            try:
                self.user_list.socket_ping(self.id)
            except PingTimeoutException:
                # We've been reaped, so disconnect.
                self.close()
                return
        elif message in ("typing", "stopped_typing"):
            self.set_typing(message == "typing")

    def on_close(self):
        # Unsubscribe here and let the exit callback handle disconnecting.
        if hasattr(self, "redis_task"):
            self.redis_task.cancel()

        if hasattr(self, "redis_client"):
            self.redis_client.close()

        if hasattr(self, "close_code") and self.close_code in (1000, 1001):
            message_type = "disconnect"
        else:
            message_type = "timeout"

        if self.joined and self.user_list.socket_disconnect(self.id, self.user_number):
            try:
                send_quit_message(self.db, redis, *self.get_chat_user(), type=message_type)
            except NoResultFound:
                send_userlist(self.db, redis, self.chat)
            self.db.commit()

        # Delete the database connection here and on_finish just to be sure.
        if hasattr(self, "_db"):
            self._db.close()
            del self._db

        if DEBUG:
            print("socket closed: %s" % (self.id))

        try:
            sockets.remove(self)
        except KeyError:
            pass

    def on_finish(self):
        if hasattr(self, "_db"):
            self._db.close()
            del self._db

    async def redis_listen(self):
        self.redis_client = await asyncio_redis.Connection.create(
            host=os.environ["REDIS_HOST"],
            port=int(os.environ["REDIS_PORT"]),
            db=int(os.environ["REDIS_DB"]),
        )
        # Set the connection name, subscribe, and listen.
        await self.redis_client.client_setname("live:%s:%s" % (self.chat_id, self.user_id))

        try:
            subscriber = await self.redis_client.start_subscribe()
            await subscriber.subscribe(list(self.channels.values()))

            while self.ws_connection:
                message = await subscriber.next_published()
                asyncio.ensure_future(self.on_redis_message(message))
        finally:
            self.redis_client.close()

    async def on_redis_message(self, message):
        if DEBUG:
            print("redis message: %s" % str(message))

        self.write_message(message.value)

        if message.channel == self.channels["user"]:
            data = json.loads(message.value)
            if "exit" in data:
                self.joined = False
                self.close()


class SearchHandler(WebSocketHandler):

    def check_origin(self, origin):
        if "localhost" in os.environ["BASE_DOMAIN"].lower():
            return True

        return origin_regex.match(origin) is not None

    def prepare(self):
        if "newparp" not in self.cookies:
            self.send_error(401)
            return

        self.searcher_id = searcher_id = self.path_args[0]
        try:
            UUID(self.path_args[0])
        except ValueError:
            self.send_error(404)
            return

        result = validate_searcher_exists(redis, self.searcher_id)
        if (
            not all(result)
            or result[0] != self.cookies["newparp"].value
        ):
            self.send_error(404)
            return

    @coroutine
    def open(self, searcher_id):
        self.redis_task = asyncio.ensure_future(self.redis_listen())
        redis.sadd("searchers", searcher_id)
        new_searcher.delay(searcher_id)

    def on_message(self, message):
        result = refresh_searcher(redis, self.searcher_id)
        if not all(result[:-2]): # -2 because filters and choices are optional
            self.close()

    async def redis_listen(self):
        self.redis_client = await asyncio_redis.Connection.create(
            host=os.environ["REDIS_HOST"],
            port=int(os.environ["REDIS_PORT"]),
            db=int(os.environ["REDIS_DB"]),
        )
        # Set the connection name, subscribe, and listen.
        await self.redis_client.client_setname("searcher:%s" % self.searcher_id)
        try:
            subscriber = await self.redis_client.start_subscribe()
            await subscriber.subscribe(["searcher:%s" % self.searcher_id])
            while self.ws_connection:
                message = await subscriber.next_published()
                asyncio.ensure_future(self.on_redis_message(message))
        finally:
            self.redis_client.close()

    async def on_redis_message(self, message):
        if DEBUG:
            print("redis message: %s" % str(message))
        self.write_message(message.value)

    def on_close(self):
        # Unsubscribe here and let the exit callback handle disconnecting.
        if hasattr(self, "redis_task"):
            self.redis_task.cancel()

        if hasattr(self, "redis_client"):
            self.redis_client.close()

        pipe = redis.pipeline()
        pipe.srem("searchers", self.searcher_id)
        pipe.delete("searcher:%s:session_id" % self.searcher_id)
        pipe.delete("searcher:%s:search_character_id" % self.searcher_id)
        pipe.delete("searcher:%s:character" % self.searcher_id)
        pipe.delete("searcher:%s:style" % self.searcher_id)
        pipe.delete("searcher:%s:levels" % self.searcher_id)
        pipe.delete("searcher:%s:filters" % self.searcher_id)
        pipe.delete("searcher:%s:choices" % self.searcher_id)
        pipe.execute()

        if DEBUG:
            print("socket closed: %s" % (self.searcher_id))

        try:
            sockets.remove(self)
        except KeyError:
            pass


class HealthHandler(RequestHandler):
    @property
    def loop(self):
        return asyncio.get_event_loop()

    def test_sql(self):
        db = sm()

        try:
            db.query(SearchCharacter).first()
        finally:
            db.close()
            del db

    def test_redis(self):
        redis.set("health", 1)

    async def get(self):
        try:
            await self.loop.run_in_executor(thread_pool, self.test_sql)
            await self.loop.run_in_executor(thread_pool, self.test_redis)
        except:
            self.send_error(500)

        self.write("ok")


def sig_handler(sig, frame):
    print("Caught signal %s." % sig)
    ioloop.add_callback_from_signal(shutdown)


def shutdown():
    print("Shutting down.")

    for socket in sockets:
        ioloop.add_callback(socket.close)

    for task in asyncio.Task.all_tasks():
        task.cancel()

    deadline = time.time() + 5

    def stop_loop():
        now = time.time()
        if now < deadline and len(sockets) != 0:
            ioloop.add_timeout(now + 0.1, stop_loop)
        else:
            ioloop.stop()

    stop_loop()

if __name__ == "__main__":

    AsyncIOMainLoop().install()
    ioloop = IOLoop.instance()

    application = Application([
        (r"/(\d+)", ChatHandler),
        (r"/search/([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})", SearchHandler),
        (r"/health", HealthHandler)
    ])

    http_server = HTTPServer(application)
    http_server.listen(int(os.environ.get("LISTEN_PORT", 5000)))

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    ioloop.start()


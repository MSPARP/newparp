from datetime import datetime
from redis import StrictRedis
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler
from uuid import uuid4

from charat2.model import sm, AnyChat, ChatUser, User
from charat2.model.connections import redis_pool

redis = StrictRedis(connection_pool=redis_pool)

class ChatHandler(WebSocketHandler):

    def prepare(self):
        self.id = str(uuid4())
        try:
            chat_id = int(self.path_args[0])
            user_id = int(redis.get("session:%s" % self.cookies["session"].value))
        except (KeyError, TypeError, ValueError):
            self.send_error(400)
            return
        self.db = sm()
        try:
            self.chat_user, self.user, self.chat = self.db.query(
                ChatUser, User, AnyChat,
            ).join(
                User, ChatUser.user_id == User.id,
            ).join(
                AnyChat, ChatUser.chat_id == AnyChat.id,
            ).filter(and_(
                ChatUser.user_id == user_id,
                ChatUser.chat_id == chat_id,
            )).one()
        except NoResultFound:
            self.send_error(404)
            return
        self.user.last_online = datetime.now()
        self.user.last_ip = self.request.headers["X-Forwarded-For"]
        if self.user.group == "banned":
            self.send_error(403)
            return

    def open(self, chat_id):
        print "socket opened:", self.id, self.chat.url, self.user.username
        self.db.commit()
        self.db.close()
        del self.db

    def on_message(self, message):
        print "message:", message

    def on_close(self):
        print "socket closed:", self.id

    def finish(self, *args, **kwargs):
        if hasattr(self, "db"):
            self.db.close()
            del self.db
        super(ChatHandler, self).finish(*args, **kwargs)

if __name__ == "__main__":
    application = Application([(r"/(\d+)", ChatHandler)])
    http_server = HTTPServer(application)
    http_server.listen(8000)
    IOLoop.instance().start()


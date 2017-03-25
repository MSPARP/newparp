import re
import hashlib
import json

from random import randint
from celery.utils.log import get_task_logger
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from newparp.helpers.chat import send_message
from newparp.model import AnyChat, ChatUser, Message, User, SpamlessFilter
from newparp.tasks import celery, WorkerTask

lists = {"reload": "0"}
logger = get_task_logger(__name__)


class Mark(Exception):
    pass


class Silence(Exception):
    pass


class CheckSpamTask(WorkerTask):
    queue = "spamless"

    def load_lists(self):
        if lists["reload"] == self.redis.get("spamless:reload"):
            return

        logger.info("reload")
        lists["reload"] = self.redis.get("spamless:reload")

        filters = self.db.query(SpamlessFilter).all()
        lists["banned_names"] = [
            re.compile(_.regex, re.IGNORECASE | re.MULTILINE)
            for _ in filters if _.type == "banned_names"
        ]
        lists["blacklist"] = [
            (re.compile(_.regex, re.IGNORECASE | re.MULTILINE), _.points)
            for _ in filters if _.type == "blacklist"
        ]
        lists["warnlist"] = [
            re.compile(_.regex, re.IGNORECASE | re.MULTILINE)
            for _ in filters if _.type == "warnlist"
        ]

    def run(self, chat_id, data):
        if len(data["messages"]) == 0:
            return

        self.load_lists()

        for message in data["messages"]:
            if message["user_number"] is None:
                continue

            message["hash"] = hashlib.md5(
                ":".join([message["color"], message["acronym"], message["text"]])
                .encode("utf-8").lower()
            ).hexdigest()

            try:
                self.check_connection_spam(chat_id, message)
                self.check_banned_names(chat_id, message)
                self.check_message_filter(chat_id, message)
                self.check_warnlist(chat_id, message)

            except Mark as e:
                q = self.db.query(Message).filter(Message.id == message["id"]).update({"spam_flag": str(e)})
                message.update({"spam_flag": str(e)})
                self.redis.publish("spamless:live", json.dumps(message))
                self.db.commit()

            except Silence as e:

                # XXX maybe cache this?
                try:
                    chat_user, user, chat = self.db.query(
                        ChatUser, User, AnyChat,
                    ).join(
                        User, ChatUser.user_id == User.id,
                    ).join(
                        AnyChat, ChatUser.chat_id == AnyChat.id,
                    ).filter(and_(
                        ChatUser.chat_id == chat_id,
                        ChatUser.number == message["user_number"],
                    )).one()
                except NoResultFound:
                    continue

                if chat.type != "group":
                    flag_suffix = chat.type.upper()
                elif chat_user.computed_group in ("admin", "creator"):
                    flag_suffix = chat_user.computed_group.upper()
                else:
                    flag_suffix = "SILENCED"

                self.db.query(Message).filter(Message.id == message["id"]).update({
                    "spam_flag": str(e) + " " + flag_suffix,
                })

                message.update({"spam_flag": str(e) + " " + flag_suffix})
                self.redis.publish("spamless:live", json.dumps(message))

                if flag_suffix == "SILENCED":
                    self.db.query(ChatUser).filter(and_(
                        ChatUser.chat_id == chat_id,
                        ChatUser.number == message["user_number"]
                    )).update({"group": "silent"})
                    send_message(self.db, self.redis, Message(
                        chat_id=chat_id,
                        type="spamless",
                        name="The Spamless",
                        acronym="\u264b",
                        text="Spam has been detected and silenced. Please come [url=http://help.msparp.com/]here[/url] or ask a chat moderator to unsilence you if this was an accident.",
                        color="626262"
                    ), True)

                self.db.commit()

    def check_connection_spam(self, chat_id, message):
        if message["type"] not in ("join", "disconnect", "timeout", "user_info"):
            return
        attempts = self.redis.increx("spamless:join:%s:%s" % (chat_id, message["user_number"]), expire=5)
        if attempts <= 10:
            return
        raise Silence("connection")

    def check_banned_names(self, chat_id, message):
        if not message["name"]:
            return
        lower_name = message["name"].lower()
        for name in lists["banned_names"]:
            if name.search(lower_name):
                raise Silence("name")

    def check_message_filter(self, chat_id, message):

        if message["type"] not in ("ic", "ooc", "me"):
            return

        message_key = "spamless:message:%s" % message["hash"]
        user_key = "spamless:blacklist:%s:%s" % (chat_id, message["user_number"])

        for phrase, points in lists["blacklist"]:
            total_points = len(phrase.findall(message["text"])) * int(points)
            self.redis.increx(message_key, expire=60, incr=total_points)
            self.redis.increx(user_key, expire=10, incr=total_points)

        message_attempts = self.redis.increx(message_key, expire=60)
        user_attempts = self.redis.increx(user_key, expire=10)

        if message_attempts >= randint(10, 35) or user_attempts >= 15:
            raise Silence("x%s" % max(message_attempts, user_attempts))
        elif message_attempts >= 10 or user_attempts >= 10:
            raise Mark("x%s" % max(message_attempts, user_attempts))

    def check_warnlist(self, chat_id, message):
        if message["type"] in ("join", "disconnect", "timeout"):
            return
        lower_text = message["text"].lower()
        for phrase in lists["warnlist"]:
            if phrase.search(lower_text):
                raise Mark("warnlist")


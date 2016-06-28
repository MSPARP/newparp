import hashlib
import uuid

from unittest import TestCase

from redis import StrictRedis
from sqlalchemy.orm.exc import NoResultFound
from exam.decorators import fixture
from exam.cases import Exam

import newparp
from newparp.model import sm, Chat, GroupChat, User
from newparp.model.connections import redis_pool


class ParpTestCase(Exam, TestCase):
    @property
    def db(self):
        if hasattr(self, "_db"):
            return self._db
        else:
            self._db = sm()
            return self._db

    @property
    def redis(self):
        if hasattr(self, "_redis"):
            return self._redis
        else:
            self._redis = StrictRedis(connection_pool=redis_pool)
            return self._redis

    @property
    def flask_client(self):
        return newparp.app.test_client()

    @classmethod
    def setUpClass(cls):
        newparp.app.config["TESTING"] = True

        if None in newparp.app.error_handler_spec[None]:
            del newparp.app.error_handler_spec[None][None]

    def create_user(self, admin=False):
        username = hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()

        new_user = User(
            username=username,
            email_address="%s@example.com" % (username),
            group="active",
            last_ip="127.0.0.1",
            admin_tier_id=1 if admin else None
        )
        new_user.set_password("hunter2")
        self.db.add(new_user)
        self.db.commit()

        return new_user

    def create_chat(self, url):
        url = url.strip()

        title = url.replace("_", " ").strip()
        lower_url = url.lower()

        try:
            chat = self.db.query(Chat.id).filter(Chat.url == lower_url).one()
            return chat
        except NoResultFound:
            pass

        new_chat = GroupChat(
            url=lower_url,
            title=title,
            creator_id=self.admin_user.id,
        )

        self.db.add(new_chat)
        self.db.commit()

        return new_chat

    @fixture
    def admin_user(self):
        return self.create_user(admin=True)

    @fixture
    def normal_user(self):
        return self.create_user()

    @fixture
    def group_chat(self):
        url = hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()
        return self.create_chat(url)

    def setUp(self):
        pass

    def tearDown(self):
        pass

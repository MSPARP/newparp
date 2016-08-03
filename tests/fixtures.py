import hashlib
import uuid

from exam.cases import Exam
from exam.decorators import fixture
from redis import StrictRedis

import newparp
from newparp.model import sm
from newparp.model.connections import redis_pool


class EnsureIP(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ["REMOTE_ADDR"] = environ.get("REMOTE_ADDR", '127.0.0.1')
        return self.app(environ, start_response)


class Fixtures(Exam):
    # Backend

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

    # Users

    @fixture
    def admin_user(self):
        return self.create_user(admin=True)

    @fixture
    def normal_user(self):
        return self.create_user()

    # Chats

    @fixture
    def group_chat(self):
        url = hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()
        return self.create_chat(url)

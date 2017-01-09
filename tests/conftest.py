import hashlib
import pytest
import uuid


from redis import StrictRedis
from sqlalchemy.orm.exc import NoResultFound

import newparp
from newparp.model import sm, Chat, GroupChat, User
from newparp.model.connections import redis_pool
from tests import create_user, create_chat

class EnsureIP(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ["REMOTE_ADDR"] = environ.get("REMOTE_ADDR", '127.0.0.1')
        return self.app(environ, start_response)


@pytest.fixture()
def app():
    newparp.app.wsgi_app = EnsureIP(newparp.app.wsgi_app)
    newparp.app.config["TESTING"] = True

    if None in newparp.app.error_handler_spec[None]:
        del newparp.app.error_handler_spec[None][None]

    return newparp.app

@pytest.fixture()
def db():
    return sm()

@pytest.fixture()
def redis():
    return StrictRedis(connection_pool=redis_pool)

@pytest.fixture()
def admin_user(db):
    return create_user(db, admin=True)

@pytest.fixture()
def normal_user(db):
    return create_user(db)

@pytest.fixture()
def group_chat(db, admin_user):
    url = hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()
    return create_chat(db, url, admin_user)
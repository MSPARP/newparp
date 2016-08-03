import hashlib
import uuid

from contextlib import contextmanager
from flask import appcontext_pushed, g
from unittest import TestCase
from sqlalchemy.orm.exc import NoResultFound

import newparp
from newparp.model import Chat, GroupChat, User
from tests.fixtures import EnsureIP, Fixtures

class ParpTestCase(Fixtures, TestCase):
    @classmethod
    def setUpClass(cls):
        newparp.app.wsgi_app = EnsureIP(newparp.app.wsgi_app)
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
        new_user.set_password("password")
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

    def login(self, username, password, client=None):
        if not client:
            client = self.flask_client

        rv = client.post("/log_in", data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

        return rv

    def setUp(self):
        pass

    def tearDown(self):
        pass

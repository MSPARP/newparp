import hashlib
import uuid

from tests import ParpTestCase

class AccountTests(ParpTestCase):
    def create_account(self, username=None, password="hunter2", password_again="hunter2"):
        if not username:
            username = hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()

        with self.flask_client as client:
            rv = self.flask_client.post("/register", data=dict(
                username=username,
                password=password,
                password_again=password_again,
                email_address="%s@example.com" % (username),
            ), environ_base={
                "REMOTE_ADDR": "192.168.1.1"
            }, follow_redirects=True)

            return rv.data

    def test_account_create(self):
        rv = self.flask_client.post("/register", data=dict(
            username=hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest(),
            password="hunter2",
            password_again="hunter2",
            email_address="%s@example.com" % (hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()),
        ), environ_base={
            "REMOTE_ADDR": "192.168.1.1"
        }, follow_redirects=True)
        self.redis.delete("register:192.168.1.1")
        assert b"log_out" in rv

    def test_too_many_registrations(self):
        rv1 = self.create_account()
        rv2 = self.create_account()
        self.redis.delete("register:192.168.1.1")
        assert b"too many registrations" in rv2

    def invalid_password(self):
        rv = self.create_account(password_again="dickbutt")
        assert b"two passwords didn't match" in rv

    def tearDown(self):
        self.redis.delete("register:192.168.1.1")

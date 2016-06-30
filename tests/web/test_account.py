import hashlib
import uuid

from tests import ParpTestCase

class AccountTests(ParpTestCase):
    def create_account(self, username=None, password="hunter2", password_again="hunter2"):
        if not username:
            username = hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()

        rv = self.flask_client.post("/register", data=dict(
            username=username,
            password=password,
            password_again=password_again,
            email_address="%s@example.com" % (username),
        ), environ_base={
            "REMOTE_ADDR": "127.0.0.1"
        }, follow_redirects=True)

        return rv

    def test_account_create(self):
        rv = self.create_account()
        self.redis.delete("register:127.0.0.1")
        assert b"log_out" in rv.data

    def test_too_many_registrations(self):
        rv1 = self.create_account()
        rv2 = self.create_account()
        self.redis.delete("register:127.0.0.1")
        assert b"too many registrations" in rv2.data

    def test_invalid_password(self):
        rv = self.create_account(password_again="dickbutt")
        assert b"two passwords didn't match" in rv.data

    def tearDown(self):
        self.redis.delete("register:127.0.0.1")

import hashlib
import uuid

from tests import ParpTestCase

class AccountTests(ParpTestCase):
    def create_account(self, username=None, password="password", password_again="password", email_address="rose@example.com"):
        if not username:
            username = hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()

        rv = self.flask_client.post("/register", data=dict(
            username=username,
            password=password,
            password_again=password_again,
            email_address=email_address,
        ), environ_base={
            "REMOTE_ADDR": "127.0.0.1"
        }, follow_redirects=True)

        return rv

    def test_account_create(self):
        rv = self.create_account()
        self.redis.delete("register:127.0.0.1")
        assert b"log_out" in rv.data

    def test_account_login(self):
        rv = self.login(self.normal_user.username, "password")
        assert b"log_out" in rv.data

    def test_too_many_registrations(self):
        self.create_account()
        rv = self.create_account()
        self.redis.delete("register:127.0.0.1")
        assert b"too many registrations" in rv.data

    # Invalid fields

    def test_invalid_password(self):
        rv = self.create_account(password_again="dickbutt")
        assert b"two passwords didn't match" in rv.data

    def test_invalid_email(self):
        rv = self.create_account(email_address="ohgodhowdidthisgethereiamnotgoodwithcomputer")
        assert b"doesn't look like a valid" in rv.data

    # Blank fields

    def test_blank_email(self):
        rv = self.create_account(email_address="")
        assert b"E-mail address is required" in rv.data

    def test_blank_password(self):
        rv = self.create_account(password="")
        assert b"enter a username and password" in rv.data

    def tearDown(self):
        self.redis.delete("register:127.0.0.1")

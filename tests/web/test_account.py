import hashlib
import uuid

from tests import login

def create_account(client, username=None, password="password", password_again="password", email_address=None):
    if not username:
        username = hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()

    if not email_address:
        email_address = "test+%s@msparp.com" % str(uuid.uuid4())

    rv = client.post("/register", data=dict(
        username=username,
        password=password,
        password_again=password_again,
        email_address=email_address,
    ), environ_base={
        "REMOTE_ADDR": "127.0.0.1"
    }, follow_redirects=True)

    return rv

def test_account_create(client, redis):
    rv = create_account(client)
    redis.delete("register:127.0.0.1")
    assert b"log_out" in rv.data

def test_account_login(client, normal_user):
    rv = login(normal_user.username, "password", client)
    assert b"log_out" in rv.data

def test_too_many_registrations(app, redis):
    with app.test_client() as client1:
        create_account(client1)

    with app.test_client() as client2:
        rv = create_account(client2)

    redis.delete("register:127.0.0.1")
    assert b"too many registrations" in rv.data

# Invalid fields

def test_invalid_password(client):
    rv = create_account(client, password_again="dickbutt")
    assert b"two passwords didn't match" in rv.data

def test_invalid_email(client):
    rv = create_account(client, email_address="ohgodhowdidthisgethereiamnotgoodwithcomputer")
    assert b"doesn't look like a valid" in rv.data

# Blank fields

def test_blank_email(client, redis):
    redis.delete("register:127.0.0.1")
    rv = create_account(client, email_address="")
    assert b"E-mail address is required" in rv.data

def test_blank_password(client, redis):
    redis.delete("register:127.0.0.1")
    rv = create_account(client, password="")
    assert b"enter a username and password" in rv.data


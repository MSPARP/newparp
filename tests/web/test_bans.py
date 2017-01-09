import random

from tests import login

# Utility

def ban(client, admin_user, address: str, reason: str="Unittest ban."):
    # Login and poke the chat to get a valid cookie and a ChatUser entry.
    login(admin_user.username, "password", client=client)
    rv = client.post("/admin/ip_bans/new", data=dict(
        address=address,
        reason=reason
    ))
    assert rv.status_code in (200, 302)

def random_ip() -> str:
    return ".".join([str(random.randint(1, 255)) for x in range(0, 4)])

# Tests

def test_no_bans(client):
    rv = client.get("/", environ_base={
        "REMOTE_ADDR": "127.0.0.1"
    })

    assert rv.status_code == 200

def test_user_ip_ban(app, client, admin_user):
    ban_ip = random_ip()

    with app.test_client() as admin_client:
        ban(admin_client, admin_user, ban_ip)

    rv = client.get("/", environ_base={
        "REMOTE_ADDR": ban_ip
    })

    print(rv.data)

    assert rv.status_code != 200
    assert b"pup-king-louie" in rv.data

def test_admin_ip_ban(client, admin_user):
    ban_ip = random_ip()

    # Login and poke the chat to get a valid cookie and a ChatUser entry.
    login(admin_user.username, "password", client=client)

    ban(client, admin_user, ban_ip)

    rv = client.get("/", environ_base={
        "REMOTE_ADDR": ban_ip
    })

    assert rv.status_code == 200
    assert b"LOL UR IP BANNED" in rv.data


import random

from tests import login

# Utility

def ban(client, address: str, reason: str="Unittest ban."):
    rv = client.post("/admin/ip_bans/new", data=dict(
        address=address,
        reason=reason
    ))
    assert rv.status_code in (200, 302)

def random_ip() -> str:
    return ".".join([str(random.randint(1, 255)) for x in range(0, 4)])

# Tests

def test_no_bans(user_client):
    rv = user_client.get("/", environ_base={
        "REMOTE_ADDR": "127.0.0.1"
    })

    assert rv.status_code == 200

def test_user_ip_ban(app, admin_client, user_client):
    ban_ip = random_ip()
    ban(admin_client, ban_ip)

    rv = user_client.get("/", environ_base={
        "REMOTE_ADDR": ban_ip
    })

    assert rv.status_code != 200
    assert b"pup-king-louie" in rv.data

def test_admin_ip_ban(admin_client):
    ban_ip = random_ip()
    ban(admin_client, ban_ip)

    rv = admin_client.get("/", environ_base={
        "REMOTE_ADDR": ban_ip
    })

    assert rv.status_code == 200
    assert b"LOL UR IP BANNED" in rv.data


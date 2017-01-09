import time

def test_front_200(client):
    rv = client.get("/")
    assert rv.status_code == 200

def test_ok_health(client):
    rv = client.get("/health")
    assert b"ok" in rv.data

def test_guest_redirect(client, group_chat):
    rv = client.get("/" + group_chat.url)
    assert b"You need to register or log in before you can join this chat" in rv.data

def test_guest_can_log(client, group_chat):
    rv = client.get("/" + group_chat.url + "/log")
    assert rv.status_code == 200

def test_nonexistant_log_404(client):
    rv = client.get("/" + str(int(time.time())))
    assert rv.status_code == 404

def test_guest_denied(client, group_chat):
    rv = client.get("/" + group_chat.url)
    assert b"need to register" in rv.data

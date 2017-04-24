import datetime
import json
import urllib.parse
import html
import uuid

from flask import g

from newparp.model import Message, Chat
from newparp.model.connections import NewparpRedis, redis_chat_pool
from newparp.model.user_list import UserListStore

def join(client, chat: Chat):
    client.get("/" + chat.url)
    user_list = UserListStore(NewparpRedis(connection_pool=redis_chat_pool), chat.id)
    user_list.socket_join(str(uuid.uuid4()), g.session_id, g.user_id)

def set_flag(client, chat_id: int, flag: str, value: str):
    rv = client.post("/chat_api/set_flag", data={
        "chat_id": chat_id,
        "flag": flag,
        "value": value,
    })
    return rv

def user_action(client, chat_id: int, action: str, number: int, reason: str=None):
    rv = client.post("/chat_api/user_action", data={
        "chat_id": chat_id,
        "action": action,
        "number": number,
        "reason": reason,
    })
    return rv

# Group creation

def test_create_new_chat(user_client):
    url = str(uuid.uuid4()).replace("-", "")
    rv = user_client.post("/create_chat", data={
        "url": url
    })
    assert rv.status_code == 302

def test_create_existing_chat(user_client):
    url = str(uuid.uuid4()).replace("-", "")
    user_client.post("/create_chat", data={
        "url": url
    })
    rv = user_client.post("/create_chat", data={
        "url": url
    })
    assert b"url_taken" in rv.data

def test_create_existing_endpoint(user_client):
    endpoints = [
        "groups",
        "admin",
        "chats",
        "characters",
        "settings",
        "log_out",
        "log_in"
    ]

    for url in endpoints:
        rv = user_client.post("/create_chat", data={
            "url": url
        })
        assert b"url_taken" in rv.data

# Flags

def test_flag_publicity_admin_only(user_client, admin_client, group_chat):
    join(admin_client, group_chat)
    set_flag(admin_client, group_chat.id, "publicity", "admin_only")

    rv = user_client.get("/" + group_chat.url)
    assert rv.status_code == 403

def test_flag_publicity_private_uninvited(user_client, admin_client, group_chat):
    join(admin_client, group_chat)
    set_flag(admin_client, group_chat.id, "publicity", "private")

    rv = user_client.get("/" + group_chat.url)
    assert rv.status_code == 403

def test_flag_publicity_private_invited(user_client, admin_client, group_chat):
    join(admin_client, group_chat)
    set_flag(admin_client, group_chat.id, "publicity", "private")
    admin_client.post("/" + group_chat.url + "/invite", data={
        "username": user_client.user.username
    })

    rv = user_client.get("/" + group_chat.url)
    assert rv.status_code == 200

# Bans

def test_action_ban_user(user_client, admin_client, group_chat):
    join(admin_client, group_chat)
    ban_id = json.loads(user_client.get("/" + group_chat.url + ".json").data.decode("utf8"))["chat_user"]["meta"]["number"]
    data = user_action(admin_client, group_chat.id, "ban", ban_id, "Unittest chat ban.")
    rv = user_client.get("/" + group_chat.url)
    assert rv.status_code == 302

# Messages

def test_send_messages(user_client, group_chat):
    join(user_client, group_chat)

    for msgtype in Message.type.property.columns[0].type.enums:
        rv = user_client.post("/chat_api/send", data={
            "chat_id": group_chat.id,
            "type": msgtype,
            "text": "This is a unit test message sent on [i]%s[/i]. Type: %s" % (
                str(datetime.datetime.now()),
                msgtype
            ),
        })
        assert rv.status_code == 204

def test_set_topic(user_client, admin_client, group_chat):
    topics = [
        "Unit testing topic created on %s" % (str(datetime.datetime.now())),
        "test overflow cutoff " * 100,
        ""
    ]

    # Topic setting with permissions

    join(admin_client, group_chat)

    for topic in topics:
        # Test if the topic is able to be set on the server side.
        rv = admin_client.post("/chat_api/set_topic", data={
            "chat_id": group_chat.id,
            "topic": topic
        })
        assert rv.status_code == 204

        # Test if the topic is set and displaying in the chat metadata.
        rv = admin_client.get("/" + group_chat.url + ".json")
        data = json.loads(rv.data.decode("utf8"))
        assert data["chat"]["topic"] == topic[:500]

    # Topic setting without permissions

    join(user_client, group_chat)
    rv = user_client.post("/chat_api/set_topic", data={
        "chat_id": group_chat.id,
        "topic": "fail"
    })
    assert rv.status_code == 403



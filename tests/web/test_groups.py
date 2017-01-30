import datetime
import json
import urllib.parse
import html

from flask import g

from newparp.model import Message
from newparp.helpers.chat import join

def fake_socket(client, group_chat):
    client.get("/" + group_chat.url)
    g.redis.sadd("chat:%s:sockets:%s" % (g.chat_id, g.session_id), "1")
    g.redis.expire("chat:%s:sockets:%s" % (g.chat_id, g.session_id), 60)

def test_send_messages(user_client, group_chat):
    fake_socket(user_client, group_chat)

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

    fake_socket(admin_client, group_chat)

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

    fake_socket(user_client, group_chat)
    rv = user_client.post("/chat_api/set_topic", data={
        "chat_id": group_chat.id,
        "topic": "fail"
    })
    assert rv.status_code == 403



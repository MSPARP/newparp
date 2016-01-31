import os
import json
import re
import requests

from charat2.tasks import celery, WorkerTask
from charat2.model import ChatUser, PushToken
from charat2.model.validators import gcm_push

def bbremove_(text):
    if hasattr(text, "groups"):
        if len(text.groups()) == 2:
            text = text.group(2)
        else:
            return

    return re.sub(r"\[([A-Za-z]+)(?:=[^\]]+)?\]([\s\S]*?)\[\/\1\]", bbremove_, text)

def bbremove(text):
    text = re.sub(r'(\[br\])+/g, "', "", text)
    text = bbremove_(text)

    return text

def safe_message(text):
    text_without_bbcode = bbremove(text)

    if len(text_without_bbcode) <= 50:
        return text_without_bbcode
    else:
        return text_without_bbcode[0:47] + "..."

@celery.task(base=WorkerTask, queue="worker")
def notify(message_dict):
    db = notify.db
    redis = notify.redis

    tokens = {
        "gcm": [],
        "other": []
    }

    users = db.query(ChatUser, PushToken).filter(ChatUser.chat_id == message_dict["chat"]["id"]).filter(ChatUser.desktop_notifications == True).filter(ChatUser.user_id == PushToken.creator_id).all()

    pipeline = redis.pipeline()

    for user, token in users:
        pipeline.rpush("user:%s:notifications" % (user.user_id), json.dumps({
            "id": message_dict["message"]["id"],
            "title": user.chat.computed_title(),
            "body": safe_message(message_dict["message"]["text"]),
            "url": "/" + user.chat.computed_url(),
            "tag": "newparp:chat:%s" % (message_dict["chat"]["id"])
        }))
        pipeline.expire("user:%s:notifications" % (user.user_id), 10)

        gcm_token = re.search("gcm/send/(.+)", token.endpoint)

        if gcm_token:
            tokens["gcm"].append({
                "user": user.user_id,
                "token": gcm_token.group(1)
            })
        else:
            tokens["other"].append({
                "user": user.user_id,
                "endpoint": token.endpoint
            })

    pipeline.execute()

    if len(tokens["gcm"]) != 0:
        notify_gcm.delay(tokens["gcm"], chat_id=message_dict["chat"]["id"])

    if len(tokens["other"]) != 0:
        notify_webpush.delay(tokens["other"], chat_id=message_dict["chat"]["id"])

@celery.task(base=WorkerTask, queue="worker")
def notify_gcm(tokens, chat_id):
    redis = notify_gcm.redis

    online = set(redis.hvals("chat:%s:online" % chat_id))
    registration_ids = [token["token"] for token in tokens if token["user"] not in online]

    if len(registration_ids) == 0:
        return

    results = requests.post("https://gcm-http.googleapis.com/gcm/send", headers={
        "Content-Type": "application/json",
        "Authorization": "key=%s" % (os.environ.get("GCM_API_KEY"))
    }, data=json.dumps({
        "registration_ids": registration_ids
    }))

    try:
        results = results.json()
    except ValueError:
        print("GCM ValueError", results.text)

@celery.task(base=WorkerTask, queue="worker")
def notify_webpush(tokens, chat_id):
    redis = notify_webpush.redis

    online = set(redis.hvals("chat:%s:online" % chat_id))
    for token in tokens:
        if token["user"] not in online:
            requests.post(token["endpoint"])

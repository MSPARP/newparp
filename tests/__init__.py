import hashlib
import uuid

from contextlib import contextmanager
from flask import appcontext_pushed, g
from unittest import TestCase
from sqlalchemy.orm.exc import NoResultFound

import newparp
from newparp.model import Chat, GroupChat, User

def login(username, password, client):
    rv = client.post("/log_in", data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

    return rv


def create_user(db, admin=False):
    username = hashlib.md5(str(uuid.uuid4()).encode("utf8")).hexdigest()

    new_user = User(
        username=username,
        email_address="%s@example.com" % (username),
        group="active",
        last_ip="127.0.0.1",
        admin_tier_id=1 if admin else None
    )
    new_user.set_password("password")
    db.add(new_user)
    db.commit()

    return new_user


def create_chat(db, url, user):
    url = url.strip()

    title = url.replace("_", " ").strip()
    lower_url = url.lower()

    try:
        chat = db.query(Chat.id).filter(Chat.url == lower_url).one()
        return chat
    except NoResultFound:
        pass

    new_chat = GroupChat(
        url=lower_url,
        title=title,
        creator_id=user.id,
    )

    db.add(new_chat)
    db.commit()

    return new_chat


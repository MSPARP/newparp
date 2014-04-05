import os
from flask import g, render_template, request

from charat2.model import GroupChat
from charat2.model.connections import use_db
from charat2.helpers.auth import login_required

@use_db
def home():
    if g.user is not None:
        return render_template("rp/home.html", rooms=rooms, base_domain=os.environ['BASE_DOMAIN'])
    else:
        return render_template("rp/register.html", rooms=rooms, base_domain=os.environ['BASE_DOMAIN'])

@use_db
@login_required
def rooms():
    rooms_query = g.db.query(GroupChat).filter(GroupChat.publicity=="listed")
    rooms = [(_, g.redis.scard("chat:%s:online" % _.id)) for _ in rooms_query]
    rooms.sort(key=lambda _: _[1], reverse=True)
    return render_template("rp/rooms.html", rooms=rooms)

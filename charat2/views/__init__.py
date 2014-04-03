from flask import g, render_template, request

from charat2.model import GroupChat
from charat2.model.connections import use_db
from charat2.helpers.auth import login_required

@use_db
def home():
    return render_template("home.html")

@use_db
def rp_home():
    if g.user is not None:
        return render_template("rp_home.html", rooms=rooms)
    else:
        url = split_url(request.url)
        domain = url['domain']
        return render_template("rp_register.html", rooms=rooms, domain=domain)

@use_db
@login_required
def rooms():
    rooms_query = g.db.query(GroupChat).filter(GroupChat.publicity=="listed")
    rooms = [(_, g.redis.scard("chat:%s:online" % _.id)) for _ in rooms_query]
    rooms.sort(key=lambda _: _[1], reverse=True)
    return render_template("rooms.html", rooms=rooms)

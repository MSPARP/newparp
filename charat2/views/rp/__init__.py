import os
from flask import g, render_template, request, redirect, url_for

from charat2.model import GroupChat
from charat2.model.connections import use_db
from charat2.helpers.auth import login_required

@use_db
def home():
    logged_in = False
    if g.user is not None:
        logged_in = True
    return render_template("rp/home.html", logged_in=logged_in, base_domain=os.environ['BASE_DOMAIN'], log_in_error=request.args.get("log_in_error"), register_error=request.args.get("register_error"))

@use_db
def rooms():
    rooms_query = g.db.query(GroupChat).filter(GroupChat.publicity=="listed")
    rooms = [(_, g.redis.scard("chat:%s:online" % _.id)) for _ in rooms_query]
    rooms.sort(key=lambda _: _[1], reverse=True)
    return render_template("rp/rooms.html", rooms=rooms)

@use_db
def logout():
    if "session" in request.cookies:
        g.redis.delete("session:" + request.cookies["session"])
    return redirect(url_for("rp_home"))


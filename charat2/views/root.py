from flask import g, render_template, request

from charat2.model.connections import use_db

@use_db
def home():
    logged_in = True if g.user is not None else False
    return render_template("home.html", logged_in=logged_in)

@use_db
def login():
    logged_in = True if g.user is not None else False
    if logged_in:
        return redirect(url_for("home"))
    else:
        return render_template("login.html", logged_in=logged_in)

@use_db
def logout():
    if "session" in request.cookies:
        g.redis.delete("session:" + request.cookies["session"])
    return redirect(url_for("home"))


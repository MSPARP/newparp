from flask import g, render_template, request, redirect, url_for

from charat2.model.connections import use_db

@use_db
def home():
    logged_in = g.user is not None
    return render_template("home.html", logged_in=logged_in)

@use_db
def login():
    logged_in = g.user is not None
    if logged_in:
        return redirect(url_for("home"))
    return render_template("login.html")

@use_db
def logout():
    if "session" in request.cookies:
        g.redis.delete("session:" + request.cookies["session"])
    return redirect(url_for("home"))


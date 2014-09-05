from bcrypt import gensalt, hashpw
from flask import g, render_template, redirect, request, url_for
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from urlparse import urlparse

from charat2.model import User
from charat2.model.connections import use_db
from charat2.model.validators import username_validator, reserved_usernames


def referer_or_home(requested=None):
    if requested:
        return requested
    if "Referer" in request.headers:
        r = urlparse(request.headers["Referer"])
        return r.scheme + "://" + r.netloc + r.path
    return url_for("home")


@use_db
def login_get():
    if g.user is not None:
        return redirect(url_for("home"))
    if request.args.get("referer"):
        referer = request.args.get("referer")
    else:
        referer = referer_or_home()
    return render_template("root/login.html", log_in_error=request.args.get("log_in_error"), referer=referer)


@use_db
def register_get():
    if g.user is not None:
        return redirect(url_for("home"))
    if request.args.get("referer"):
        referer = request.args.get("referer")
    else:
        referer = referer_or_home()
    return render_template("root/register.html", register_error=request.args.get("register_error"), referer=referer)


@use_db
def login_post():
    # Check username, lowercase to make it case-insensitive.
    referer = None
    getreferer = ""
    if "referer" in request.form:
        referer = request.form["referer"]
        getreferer = "&referer=" + referer
    try:
        user = g.db.query(User).filter(
            func.lower(User.username) == request.form["username"].lower()
        ).one()
    except NoResultFound:
        return redirect(referer_or_home() + "?log_in_error=The username or password you entered is incorrect." + getreferer)
    # Check password.
    if hashpw(
        request.form["password"].encode(),
        user.password.encode()
    ) != user.password:
        return redirect(referer_or_home() + "?log_in_error=The username or password you entered is incorrect." + getreferer)
    g.redis.set("session:" + g.session_id, user.id)
    return redirect(referer_or_home(referer))


@use_db
def logout():
    if "session" in request.cookies:
        g.redis.delete("session:" + request.cookies["session"])
    return redirect(referer_or_home())


@use_db
def register():
    referer = None
    getreferer = ""
    if "referer" in request.form:
        referer = request.form["referer"]
        getreferer = "&referer=" + referer
    # Don't accept blank fields.
    if request.form["username"] == "" or request.form["password"] == "":
        return redirect(referer_or_home() + "?register_error=Please enter a username and password." + getreferer)
    # Make sure the two passwords match.
    if request.form["password"] != request.form["password_again"]:
        return redirect(referer_or_home() + "?register_error=The two passwords didn't match." + getreferer)
    # Check username against username_validator.
    # Silently truncate it because the only way it can be longer is if they've hacked the front end.
    username = request.form["username"][:50]
    if username_validator.match(username) is None:
        return redirect(referer_or_home() + "?register_error=Usernames can only contain letters, numbers, hyphens and underscores." + getreferer)
    # XXX DON'T ALLOW USERNAMES STARTING WITH GUEST_.
    # Make sure this username hasn't been taken before.
    # Also check against reserved usernames.
    existing_username = g.db.query(User.id).filter(
        func.lower(User.username) == username.lower()
    ).count()
    if existing_username == 1 or username in reserved_usernames:
        return redirect(referer_or_home() + "?register_error=The username " + username + " has already been taken." + getreferer)
    new_user = User(
        username=username,
        password=hashpw(request.form["password"].encode(), gensalt()),
    )
    g.db.add(new_user)
    g.db.flush()
    g.redis.set("session:" + g.session_id, new_user.id)
    g.db.commit()
    return redirect(referer_or_home(request.form["referer"]))


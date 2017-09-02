from bcrypt import gensalt, hashpw
from flask import abort, g, jsonify, render_template, redirect, request, url_for
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from newparp.helpers import alt_formats
from newparp.helpers.auth import not_logged_in_required
from newparp.helpers.email import send_email
from newparp.model import User
from newparp.model.connections import use_db
from newparp.model.validators import username_validator, email_validator, reserved_usernames


def referer_or_home():
    if "Referer" in request.headers:
        r = urlparse(request.headers["Referer"])
        return r.scheme + "://" + r.netloc + r.path
    return url_for("home")


@not_logged_in_required
def log_in_get():
    return render_template("account/log_in.html")


@alt_formats({"json"})
@not_logged_in_required
@use_db
def log_in_post(fmt=None):

    # Check username, lowercase to make it case-insensitive.
    try:
        user = g.db.query(User).filter(
            func.lower(User.username) == request.form["username"].lower()
        ).one()
    except NoResultFound:
        if fmt == "json":
            return jsonify({"error": "no_user"}), 400
        return redirect(referer_or_home() + "?log_in_error=no_user")

    # Check password.
    if not user.check_password(request.form["password"]):
        if fmt == "json":
            return jsonify({"error": "wrong_password"}), 400
        return redirect(referer_or_home() + "?log_in_error=wrong_password")

    g.redis.set("session:" + g.session_id, user.id, 2592000)

    if fmt == "json":
        return jsonify(user.to_dict(include_options=True))

    redirect_url = referer_or_home()
    # Make sure we don't go back to the log in page.
    if redirect_url == url_for("log_in", _external=True):
        return redirect(url_for("home"))
    return redirect(redirect_url)


def log_out():
    if "newparp" in request.cookies:
        g.redis.delete("session:" + request.cookies["newparp"])
        g.redis.delete("session:" + request.cookies["newparp"] + ":csrf")
    return redirect(referer_or_home())


@not_logged_in_required
def register_get():
    return render_template("account/register.html")

@not_logged_in_required
def forgot_password_get():
    return render_template("account/forgot_password.html")

@not_logged_in_required
@use_db
def forgot_password_post():

    if g.redis.get("reset_password_limit:%s" % request.environ["REMOTE_ADDR"]):
        return redirect(referer_or_home() + "?error=limit")

    try:
        user = g.db.query(User).filter(User.username == request.form["username"].lower()).one()
       
    except NoResultFound:
        return redirect(referer_or_home() + "?error=no_user&username=" + request.form['username'])

    if g.redis.get("reset_password_limit:%s" % user.id):
        return redirect(referer_or_home() + "?error=limit")

    if not user.email_address:
        return redirect(referer_or_home() + "?error=no_email")

    if not user.email_verified:
        return redirect(referer_or_home() + "?error=no_verify")

    g.user = user
    send_email("reset", g.user.email_address)
    g.redis.setex("reset_password_limit:%s" % request.environ["REMOTE_ADDR"], 86400, 1)
    g.redis.setex("reset_password_limit:%s" % user.id, 86400, 1)

    return redirect(referer_or_home() + "?error=success")

@not_logged_in_required
def reset_password_get():
    user = _validate_reset_token(request)
    return render_template("account/reset_password.html")

@use_db
def reset_password_post():
    user = _validate_reset_token(request)

    if not request.form["password"]:
        return redirect(referer_or_home() + "?error=no_password")

    if request.form["password"] != request.form["password_again"]:
        return redirect(referer_or_home() + "?error=passwords_didnt_match")

    user.password = hashpw(request.form["password"].encode(), gensalt()).decode()

    g.redis.delete("reset_password:%s:%s" % (user.id, request.args.get["email_address"].strip()))

    response = HTTPFound(request.route_path("home"))

    new_session_id = str(uuid4())
    g.redis.set("session:"+new_session_id, user.id)
    response.set_cookie("newparp", new_session_id, 31536000)

    return response

@use_db
def _validate_reset_token(request):
    try:
        user_id = int(request.args["user_id"].strip())
        email_address = request.args["email_address"].strip()
        token = request.args["token"].strip()
    except (KeyError, ValueError):
        return("1")
    stored_token = g.redis.get("reset_password:%s:%s" % (user_id, email_address))
    if not user_id or not email_address or not token or not stored_token:
        return("2")
    stored_token = stored_token.decode("utf-8")

    if not stored_token == token:
        return("3")

    try:
        return g.db.query(User).filter(User.id == user_id).one()
    except NoResultFound:
        return("4")


@not_logged_in_required
@use_db
def register_post():

    if g.redis.exists("register:" + request.headers.get("X-Forwarded-For", request.remote_addr)):
        return redirect(referer_or_home() + "?register_error=ip")

    # Don't accept blank fields.
    if request.form["username"] == "" or request.form["password"] == "":
        return redirect(referer_or_home() + "?register_error=blank")

    # Make sure the two passwords match.
    if request.form["password"] != request.form["password_again"]:
        return redirect(referer_or_home() + "?register_error=passwords_didnt_match")

    # Check email address against email_validator.
    # Silently truncate it because the only way it can be longer is if they've hacked the front end.
    email_address = request.form.get("email_address").strip()[:100]
    if not email_address:
        return redirect(referer_or_home() + "?register_error=blank_email")
    if email_validator.match(email_address) is None:
        return redirect(referer_or_home() + "?register_error=invalid_email")

    # Make sure this email address hasn't been taken before.
    if g.db.query(User.id).filter(
        func.lower(User.email_address) == email_address.lower()
    ).count() != 0:
        return redirect(referer_or_home() + "?register_error=email_taken")

    # Check username against username_validator.
    # Silently truncate it because the only way it can be longer is if they've hacked the front end.
    username = request.form["username"][:50]
    if username_validator.match(username) is None:
        return redirect(referer_or_home() + "?register_error=invalid_username")

    # Make sure this username hasn't been taken before.
    # Also check against reserved usernames.
    if username.startswith("guest_") or g.db.query(User.id).filter(
        func.lower(User.username) == username.lower()
    ).count() == 1 or username.lower() in reserved_usernames:
        return redirect(referer_or_home() + "?register_error=username_taken")

    new_user = User(
        username=username,
        email_address=email_address,
        group="new",
        last_ip=request.headers.get("X-Forwarded-For", request.remote_addr),
    )
    new_user.set_password(request.form["password"])
    g.db.add(new_user)
    g.db.flush()
    g.redis.set("session:" + g.session_id, new_user.id, 2592000)
    g.redis.setex("register:" + request.headers.get("X-Forwarded-For", request.remote_addr), 86400, 1)

    g.user = new_user
    send_email("welcome", email_address)

    g.db.commit()

    redirect_url = referer_or_home()
    # Make sure we don't go back to the log in page.
    if redirect_url == url_for("register", _external=True):
        return redirect(url_for("home"))
    return redirect(redirect_url)


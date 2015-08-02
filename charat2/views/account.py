from bcrypt import gensalt, hashpw
from flask import abort, g, jsonify, render_template, redirect, request, url_for
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from charat2.helpers import alt_formats
from charat2.helpers.auth import log_in_required, not_logged_in_required
from charat2.model import User
from charat2.model.connections import use_db
from charat2.model.validators import username_validator, email_validator, reserved_usernames, secret_answer_replacer


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
    if hashpw(
        request.form["password"].encode("utf8"),
        user.password.encode()
    ) != user.password:
        if fmt == "json":
            return jsonify({"error": "wrong_password"}), 400
        return redirect(referer_or_home() + "?log_in_error=wrong_password")

    g.redis.set("session:" + g.session_id, user.id)

    if fmt == "json":
        return jsonify(user.to_dict(include_options=True))

    redirect_url = referer_or_home()
    # Make sure we don't go back to the log in page.
    if redirect_url == url_for("log_in", _external=True):
        return redirect(url_for("home"))
    return redirect(redirect_url)


def log_out():
    if "session" in request.cookies:
        g.redis.delete("session:" + request.cookies["session"])
        g.redis.delete("session:" + request.cookies["session"] + ":csrf")
    return redirect(referer_or_home())


@not_logged_in_required
def register_get():
    return render_template("account/register.html")


@not_logged_in_required
@use_db
def register_post():

    if g.redis.exists("register:" + request.headers["X-Forwarded-For"]):
        return redirect(referer_or_home() + "?register_error=ip")

    # Don't accept blank fields.
    if request.form["username"] == "" or request.form["password"] == "":
        return redirect(referer_or_home() + "?register_error=blank")

    # Make sure the two passwords match.
    if request.form["password"] != request.form["password_again"]:
        return redirect(referer_or_home() + "?register_error=passwords_didnt_match")

    # Check email address against email_validator.
    # Silently truncate it because the only way it can be longer is if they've hacked the front end.
    email_address = request.form["email_address"].strip()[:100]
    if email_address != "" and email_validator.match(email_address) is None:
        return redirect(referer_or_home() + "?register_error=invalid_email")

    # Check username against username_validator.
    # Silently truncate it because the only way it can be longer is if they've hacked the front end.
    username = request.form["username"][:50]
    if username_validator.match(username) is None:
        return redirect(referer_or_home() + "?register_error=invalid_username")

    # XXX DON'T ALLOW USERNAMES STARTING WITH GUEST_.
    # Make sure this username hasn't been taken before.
    # Also check against reserved usernames.
    existing_username = g.db.query(User.id).filter(
        func.lower(User.username) == username.lower()
    ).count()
    if existing_username == 1 or username.lower() in reserved_usernames:
        return redirect(referer_or_home() + "?register_error=username_taken")

    new_user = User(
        username=username,
        password=hashpw(request.form["password"].encode("utf8"), gensalt()),
        secret_question=request.form["secret_question"][:50],
        secret_answer=hashpw(
            secret_answer_replacer.sub("", request.form["secret_answer"].lower()).encode("utf8"),
            gensalt(),
        ),
        email_address=email_address if email_address != "" else None,
        # XXX uncomment this when we release it to the public.
        #group="active",
        last_ip=request.headers["X-Forwarded-For"],
    )
    g.db.add(new_user)
    g.db.flush()
    g.redis.set("session:" + g.session_id, new_user.id)
    g.redis.setex("register:" + request.headers["X-Forwarded-For"], 86400, 1)
    g.db.commit()

    redirect_url = referer_or_home()
    # Make sure we don't go back to the log in page.
    if redirect_url == url_for("register", _external=True):
        return redirect(url_for("home"))
    return redirect(redirect_url)


@not_logged_in_required
@use_db
def reset_password_get():
    username = request.args.get("username", "").strip()[:50].lower()
    if not username:
        return render_template("account/reset_password.html")
    try:
        user = g.db.query(User).filter(func.lower(User.username) == username).one()
    except NoResultFound:
        return render_template("account/reset_password.html", error="no_user")
    return render_template("account/secret_question.html", user=user)


@not_logged_in_required
@use_db
def reset_password_post():

    try:
        user = g.db.query(User).filter(
            func.lower(User.username) == request.form["username"].lower(),
        ).one()
    except NoResultFound:
        abort(404)

    # Verify secret answer.
    if hashpw(
        secret_answer_replacer.sub("", request.form["secret_answer"].lower()).encode("utf8"),
        user.secret_answer.encode(),
    ) != user.secret_answer:
        return render_template("account/secret_question.html", user=user, error="wrong_answer")

    # Don't accept a blank password.
    if request.form["password"] == "":
        return render_template("account/secret_question.html", user=user, error="blank")

    # Make sure the two passwords match.
    if request.form["password"] != request.form["password_again"]:
        return render_template("account/secret_question.html", user=user, error="passwords_didnt_match")

    user.password = hashpw(request.form["password"].encode("utf8"), gensalt())

    return redirect(url_for("log_in"))


@use_db
@log_in_required
def settings_get():
    return render_template("account/settings.html")

@use_db
@log_in_required
def settings_post():
    g.user.confirm_disconnect = "confirm_disconnect" in request.form
    g.user.desktop_notifications = "desktop_notifications" in request.form
    g.user.show_system_messages = "show_system_messages" in request.form
    g.user.show_bbcode = "show_bbcode" in request.form
    g.user.show_preview = "show_preview" in request.form
    g.user.typing_notifications = "typing_notifications" in request.form
    return redirect(url_for("settings"))


timezones = {
    "Africa/Johannesburg", "Africa/Lagos", "Africa/Windhoek", "America/Adak",
    "America/Anchorage", "America/Argentina/Buenos_Aires", "America/Bogota",
    "America/Caracas", "America/Chicago", "America/Denver", "America/Godthab",
    "America/Guatemala", "America/Halifax", "America/Los_Angeles",
    "America/Montevideo", "America/New_York", "America/Noronha",
    "America/Noronha", "America/Phoenix", "America/Santiago",
    "America/Santo_Domingo", "America/St_Johns", "Asia/Baghdad", "Asia/Baku",
    "Asia/Beirut", "Asia/Dhaka", "Asia/Dubai", "Asia/Irkutsk", "Asia/Jakarta",
    "Asia/Kabul", "Asia/Kamchatka", "Asia/Karachi", "Asia/Kathmandu",
    "Asia/Kolkata", "Asia/Krasnoyarsk", "Asia/Omsk", "Asia/Rangoon",
    "Asia/Shanghai", "Asia/Tehran", "Asia/Tokyo", "Asia/Vladivostok",
    "Asia/Yakutsk", "Asia/Yekaterinburg", "Atlantic/Azores",
    "Atlantic/Cape_Verde", "Australia/Adelaide", "Australia/Brisbane",
    "Australia/Darwin", "Australia/Eucla", "Australia/Eucla",
    "Australia/Lord_Howe", "Australia/Sydney", "Etc/GMT+12", "Europe/Berlin",
    "Europe/London", "Europe/Moscow", "Pacific/Apia", "Pacific/Apia",
    "Pacific/Auckland", "Pacific/Chatham", "Pacific/Easter", "Pacific/Gambier",
    "Pacific/Honolulu", "Pacific/Kiritimati", "Pacific/Majuro",
    "Pacific/Marquesas", "Pacific/Norfolk", "Pacific/Noumea",
    "Pacific/Pago_Pago", "Pacific/Pitcairn", "Pacific/Tongatapu", "UTC",
}


@use_db
@log_in_required
def settings_timezone():
    if request.form["timezone"] in timezones:
        g.user.timezone = request.form["timezone"]
    return "", 204


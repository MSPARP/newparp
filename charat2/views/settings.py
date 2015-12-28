from flask import g, redirect, render_template, request, url_for
from sqlalchemy import and_

from charat2.helpers import alt_formats, themes
from charat2.helpers.auth import log_in_required
from charat2.model import Block
from charat2.model.connections import use_db

@use_db
@log_in_required
def home_get():
    return render_template(
        "settings/home.html",
        timezones=sorted(list(timezones)),
        themes=themes,
    )

@use_db
@log_in_required
def home_post():
    g.user.confirm_disconnect = "confirm_disconnect" in request.form
    g.user.desktop_notifications = "desktop_notifications" in request.form
    g.user.show_system_messages = "show_system_messages" in request.form
    g.user.show_bbcode = "show_bbcode" in request.form
    g.user.show_timestamps = "show_timestamps" in request.form
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
def timezone():
    if request.form["timezone"] in timezones:
        g.user.timezone = request.form["timezone"]
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return "", 204
    return redirect(url_for("settings"))


@use_db
@log_in_required
def theme():
    if request.form["theme"] in themes:
        g.user.theme = request.form["theme"]
    else:
        g.user.theme = None
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return "", 204
    return redirect(url_for("settings"))


@use_db
@log_in_required
def log_in_details():
    return render_template("settings/log_in_details.html")


@use_db
@log_in_required
def change_password():

    if (
        not request.form.get("old_password")
        or not request.form.get("new_password")
        or not request.form.get("new_password_again")
    ):
        return render_template("settings/log_in_details.html", error="blank_password")
        return redirect(url_for("settings_log_in_details"))

    if request.form["new_password"] != request.form["new_password_again"]:
        return render_template("settings/log_in_details.html", error="passwords_didnt_match")

    if not g.user.check_password(request.form["old_password"]):
        return render_template("settings/log_in_details.html", error="wrong_password")

    g.user.set_password(request.form["new_password"])

    return redirect(url_for("settings_log_in_details", saved="password"))


@use_db
@log_in_required
def blocks():
    return render_template(
        "settings/blocks.html",
        blocks=g.db.query(Block).order_by(Block.created.desc()).all(),
    )


@use_db
@log_in_required
def unblock():
    g.db.query(Block).filter(and_(
        Block.blocking_user_id == g.user.id,
        # created date because the client mustn't know the blocked_user_id
        Block.created == request.form["created"],
    )).delete()
    return redirect(url_for("settings_blocks"))


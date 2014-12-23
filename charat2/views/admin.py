from flask import g, redirect, render_template, request, url_for

from charat2.helpers.auth import admin_required
from charat2.model.connections import use_db


@use_db
@admin_required
def announcements_get():
    return render_template("admin/announcements.html")


@use_db
@admin_required
def announcements_post():
    g.redis.set("announcements", request.form["announcements"])
    return redirect(url_for("admin_announcements"))


from flask import render_template

from charat2.helpers.auth import admin_required
from charat2.model.connections import use_db


@use_db
@admin_required
def home():
    return render_template("admin/spamless/home.html")


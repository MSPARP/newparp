import json

from flask import g, render_template, request, redirect, url_for

from charat2.model.connections import use_db


@use_db
def home():
    return render_template(
        "root/home.html",
    )


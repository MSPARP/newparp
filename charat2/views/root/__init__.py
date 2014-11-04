import json

from flask import g, render_template, request, redirect, url_for

from charat2.model.connections import use_db


@use_db
def home():
    if g.user is None:
        return render_template("root/home_guest.html")
    return render_template("root/home.html")


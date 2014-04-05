from flask import g, render_template, request

from charat2.model.connections import use_db

@use_db
def home():
    logged_in = True if g.user is None else False
    return render_template("home.html", logged_in=logged_in)


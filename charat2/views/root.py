from flask import g, render_template, request

from charat2.model.connections import use_db

@use_db
def home():
    return render_template("home.html")


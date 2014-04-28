import json

from flask import g, render_template, request, redirect, url_for

from charat2.model.connections import use_db

from urllib import urlopen
import json

@use_db
def home():
    jsonurl = urlopen("http://charat.thae.li/feed.json")
    posts = json.loads(jsonurl.read())
    return render_template(
        "home.html",
        logged_in=g.user is not None,
        posts=posts
    )


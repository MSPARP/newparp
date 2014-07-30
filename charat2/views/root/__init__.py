import json

from flask import g, render_template, request, redirect, url_for

from charat2.model.connections import use_db
from charat2.views import blog

@use_db
def home():
    posts = json.loads(blog.feed())
    return render_template(
        "root/home.html",
        posts=posts
    )


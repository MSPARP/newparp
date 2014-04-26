import json

from flask import g, render_template, request, redirect, url_for

from charat2.model.connections import use_db

@use_db
def home():
    return render_template(
        "home.html",
        logged_in=g.user is not None,
    )

@use_db
def feed():
    data = [{
        "id" : 1,
        "title" : "Test Blog",
        "author" : "Sho Tran",
        "content" : "lorem ipsum testing everything"
    },
    {
        "id" : 2,
        "title" : "Test Bloggy Stuff",
        "author" : "Sho Tran",
        "content" : "lorem ipsum testing everything yyyyeee"
    }]
    return json.dumps(data, sort_keys=True)


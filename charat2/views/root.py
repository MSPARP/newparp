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
    data = []
    for i in range(1,50):
        post = {
            "id" : i,
            "title" : "Test Blog "+i,
            "author" : "Sho Tran",
            "content" : "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        }
        data.append(post)
    return json.dumps(data, sort_keys=True)


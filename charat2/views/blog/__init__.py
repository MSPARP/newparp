import json

from flask import abort, g, render_template, request, redirect, url_for

from charat2.model.connections import use_db

@use_db
def home():
    posts = json.loads(feed())
    return render_template(
        "blog/home.html",
        logged_in=g.user is not None,
        posts=posts
    )

@use_db
def view_post(id,title_path=None):
    posts = json.loads(feed())
    if id in posts:
        post = posts[id]
    else:
        abort(404)
    return render_template(
        "blog/post.html",
        logged_in=g.user is not None,
        post=post
    )

@use_db
def feed():
    data = {
    1 : {
        "id" : 1,
        "title" : "Test Blog",
        "author" : "Sho Tran",
        "content" : "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    },
    2 : {
        "id" : 2,
        "title" : "Test Bloggy Stuff",
        "author" : "Sho Tran",
        "content" : "lorem ipsum testing everything yyyyeee"
    },
    3 : {
        "id" : 3,
        "title" : "Test Bloggy Stuff",
        "author" : "Sho Tran",
        "content" : "lorem ipsum testing everything yyyyeee"
    },
    4 : {
        "id" : 4,
        "title" : "Test Bloggy Stuff",
        "author" : "Sho Tran",
        "content" : "lorem ipsum testing everything yyyyeee"
    },
    5 : {
        "id" : 5,
        "title" : "New blog post",
        "author" : "Sho Tran",
        "content" : "BUT LIKE, duuuude, look at this post, it's like all long and lasdjfasdjkalksdjfl;ajsdo;fj... DID YOU LKNOAOSIDF EVERYTHING MWAHAHAHAHAHAHAHAHAHAHAHAHAHHAHA"
    }}
    return json.dumps(data, sort_keys=True)

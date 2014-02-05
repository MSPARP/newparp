from flask import g, render_template

def home():
    if g.user is not None:
        return render_template("home.html")
    else:
        return render_template("register.html")


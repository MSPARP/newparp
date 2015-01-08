from flask import abort, g, render_template, request, url_for
from functools import wraps


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None or g.user.group != "admin":
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


def log_in_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return render_template("account/log_in_required.html")
        elif g.user.group == "guest":
            return render_template("account/activation_required.html")
        return f(*args, **kwargs)
    return decorated_function


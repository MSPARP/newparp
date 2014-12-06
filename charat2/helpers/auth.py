from flask import abort, g, render_template, request, url_for
from functools import wraps


def log_in_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return render_template("account/log_in_required.html")
        return f(*args, **kwargs)
    return decorated_function


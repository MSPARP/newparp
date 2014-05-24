from flask import abort, g, redirect, request, url_for
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login_get')+"?referer="+request.path)
        return f(*args, **kwargs)
    return decorated_function


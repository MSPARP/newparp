from flask import abort, g, redirect, request, url_for
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login_get')+"?log_in_error=You need to be logged in to access this page.&referer="+request.url)
        return f(*args, **kwargs)
    return decorated_function


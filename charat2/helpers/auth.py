from flask import abort, g
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


from flask import abort, g, render_template, redirect, request, url_for
from functools import wraps
from sqlalchemy import and_, func

from newparp.model import AdminTierPermission


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return render_template("account/log_in_required.html")
        elif not g.user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def log_in_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return render_template("account/log_in_required.html")
        elif g.user.group == "new":
            return render_template("account/user_new.html")
        elif g.user.group == "deactivated":
            return render_template("account/user_deactivated.html")
        return f(*args, **kwargs)
    return decorated_function


def not_logged_in_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user_id is not None:
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                return render_template("account/log_in_required.html")
            elif not g.user.has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


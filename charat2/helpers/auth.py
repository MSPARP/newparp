from flask import abort, g, render_template, request, url_for
from functools import wraps
from sqlalchemy import and_, func

from charat2.model import AdminTierPermission


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
        elif g.user.group == "guest":
            return render_template("account/activation_required.html")
        return f(*args, **kwargs)
    return decorated_function


def not_logged_in_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user_id is not None:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                return render_template("account/log_in_required.html")
            elif not g.user.is_admin or g.user.admin_tier_id is None:
                abort(403)
            elif g.db.query(func.count("*")).select_from(AdminTierPermission).filter(and_(
                AdminTierPermission.admin_tier_id == g.user.admin_tier_id,
                AdminTierPermission.permission == permission,
            )).scalar() == 0:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


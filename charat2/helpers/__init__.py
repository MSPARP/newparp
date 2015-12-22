import os
from collections import OrderedDict
from flask import abort, g, redirect, request, url_for
from functools import wraps


themes = OrderedDict([
    ("default_monochrome", "Default (monochrome)"),
    ("darkskin", "Dark skin"),
    ("darkskin_monochrome", "Dark skin (monochrome)"),
    ("gristmas", "Gristmas"),
    ("gristmas_noanimate", "Gristmas (No animations)"),
    ("gristmas_dark", "Dark Gristmas"),
    ("gristmas_dark_noanimate", "Dark Gristmas (No animations)"),
])


def check_csrf_token():
    # Check CSRF only for POST requests.
    if request.method != "POST":
        return

    # Ignore CSRF only for local debugging.
    if 'NOCSRF' in os.environ:
        return

    token = g.redis.get("session:%s:csrf" % g.session_id)
    if "token" in request.form and request.form["token"] == token:
        return
    abort(403)


def alt_formats(available_formats):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "fmt" in kwargs:
                # Redirect to no extension if extension is html.
                if kwargs["fmt"] == "html":
                    del kwargs["fmt"]
                    return redirect(url_for(request.endpoint, **kwargs))
                if kwargs["fmt"] not in available_formats:
                    abort(412)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def tags_to_set(tag_string):
    tags = set()
    for tag in tag_string.split(","):
        tag = tag.strip()
        if tag == "":
            continue
        # Silently truncate to 100 because we need a limit in the database and
        # people are unlikely to type that much.
        tags.add(tag.lower()[:100])
    return tags


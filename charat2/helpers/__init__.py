from flask import abort, redirect, request, url_for
from functools import wraps

def alt_formats(available_formats=set([])):
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


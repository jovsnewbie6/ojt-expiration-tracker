from functools import wraps

from flask import abort, redirect, url_for
from flask_login import current_user


def permission_required(permission_name):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.admin_login"))

            if not getattr(current_user, "has_permission", lambda _: False)(permission_name):
                abort(403)

            return view(*args, **kwargs)

        return wrapped

    return decorator

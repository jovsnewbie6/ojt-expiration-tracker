from functools import wraps
import logging

from flask import abort, redirect, url_for, current_app
from flask_login import current_user
from sqlalchemy import text

logger = logging.getLogger(__name__)


def check_database_connection():
    """Verify database is accessible before performing critical operations."""
    try:
        from app import db
        # Attempt a simple database query
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        return True, None
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False, str(e)


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

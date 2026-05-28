from functools import wraps
import logging
import time

from flask import abort, redirect, url_for, current_app
from flask_login import current_user
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, DatabaseError, TimeoutError as SQLTimeoutError

logger = logging.getLogger(__name__)


def check_database_connection(max_retries=2):
    """Verify database is accessible before performing critical operations.
    
    Retries connection if it fails (handles transient connection issues on Render).
    """
    try:
        from app import db
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Database connection check (attempt {attempt + 1}/{max_retries})...")
                # Attempt a simple database query
                db.session.execute(text("SELECT 1"))
                db.session.commit()
                logger.debug("Database connection check successful")
                return True, None
            except (OperationalError, DatabaseError, SQLTimeoutError) as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
                # Close the connection to force a new one on retry
                try:
                    db.session.close()
                    db.engine.dispose()  # Close all connections in the pool
                except Exception as dispose_error:
                    logger.debug(f"Could not dispose engine: {dispose_error}")
                
                if attempt < max_retries - 1:
                    # Wait before retrying
                    time.sleep(0.5)
                    continue
                else:
                    logger.error(f"Database connection failed after {max_retries} attempts: {str(e)}")
                    return False, str(e)
            except Exception as e:
                logger.error(f"Unexpected error during connection check: {str(e)}")
                return False, str(e)
        
        return False, "Connection check failed"
    except Exception as e:
        logger.error(f"Fatal error in check_database_connection: {str(e)}")
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

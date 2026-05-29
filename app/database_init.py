"""Database initialization and health check utilities."""
import logging
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError

from app import db

logger = logging.getLogger(__name__)


def initialize_database():
    """
    SAFE VERSION:
    - DOES NOT create tables
    - ONLY checks schema state
    - Relies on Flask-Migrate (flask db upgrade)
    """
    try:
        logger.info("Checking database schema...")

        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        logger.info(f"Existing tables: {existing_tables}")

        critical_tables = [
            "users",
            "students",
            "student_records",
            "permissions"
        ]

        missing_tables = [t for t in critical_tables if t not in existing_tables]

        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
            logger.warning("Run 'flask db upgrade' to initialize database schema")
            return False

        logger.info("✓ Database schema is valid")
        return True

    except OperationalError as e:
        logger.error(f"Database connection error: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected database error: {e}", exc_info=True)
        return False


def check_database_health():
    """
    Lightweight DB connection + schema validation
    """
    try:
        db.session.execute(text("SELECT 1"))

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        required = ["users", "students", "student_records", "permissions"]
        missing = [t for t in required if t not in tables]

        if missing:
            return False, f"Missing tables: {missing}"

        return True, None

    except OperationalError as e:
        return False, f"DB connection error: {str(e)[:100]}"

    except Exception as e:
        return False, f"DB error: {str(e)[:100]}"
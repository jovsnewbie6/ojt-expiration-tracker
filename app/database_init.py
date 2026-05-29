"""Database initialization and health check utilities."""
import logging
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app import db

logger = logging.getLogger(__name__)


# -----------------------------
# SAFE DATABASE INITIALIZATION CHECK
# -----------------------------
def initialize_database():
    """
    SAFE VERSION:
    - Does NOT create tables
    - Only validates schema existence safely
    - Works with Flask-Migrate (flask db upgrade)
    """
    try:
        logger.info("Checking database schema...")

        # SAFE query instead of inspect(db.engine)
        result = db.session.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )

        existing_tables = [row[0] for row in result.fetchall()]
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
            logger.warning("Run 'flask db upgrade' to initialize schema")
            return False

        logger.info("✓ Database schema is valid")
        return True

    except (OperationalError, ProgrammingError) as e:
        logger.error(f"Database schema check failed: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected database error: {e}", exc_info=True)
        return False


# -----------------------------
# LIGHTWEIGHT HEALTH CHECK
# -----------------------------
def check_database_health():
    """
    Fast DB connection + schema validation
    Safe for Render startup
    """
    try:
        # 1. Connection check
        db.session.execute(text("SELECT 1"))

        # 2. Schema check (safe version)
        result = db.session.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )

        tables = [row[0] for row in result.fetchall()]

        required = ["users", "students", "student_records", "permissions"]
        missing = [t for t in required if t not in tables]

        if missing:
            return False, f"Missing tables: {missing}"

        return True, None

    except OperationalError as e:
        return False, f"DB connection error: {str(e)[:120]}"

    except Exception as e:
        return False, f"DB error: {str(e)[:120]}"


# -----------------------------
# OPTIONAL SAFE HELPER (FOR RENDER BOOTSTRAP)
# -----------------------------
def ensure_database_ready():
    """
    Used during login/registration flows.
    Prevents crashes if DB is temporarily unavailable.
    """
    try:
        ok, error = check_database_health()
        if not ok:
            logger.warning(f"Database not ready: {error}")
            return False
        return True

    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
        return False
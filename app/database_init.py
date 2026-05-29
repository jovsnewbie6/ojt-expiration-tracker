"""Database initialization and health check utilities."""
import logging
from flask import current_app
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


def initialize_database():
    """
    Initialize database tables safely.
    
    This is called during app startup to ensure all tables exist.
    Works both locally and on Render.
    """
    from app import db
    
    try:
        logger.info("Starting database initialization...")
        
        # First, try to check if tables already exist
        try:
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"Existing tables: {existing_tables}")
            
            # Check if critical tables exist
            critical_tables = ['users', 'students', 'student_records']
            missing_tables = [t for t in critical_tables if t not in existing_tables]
            
            if not missing_tables:
                logger.info("✓ All critical tables exist")
                return True
            
            logger.warning(f"Missing tables: {missing_tables}")
            
        except Exception as e:
            logger.warning(f"Could not inspect tables: {e}")
        
        # Try to create all tables
        logger.info("Attempting to create tables with db.create_all()...")
        db.create_all()
        logger.info("✓ Database tables created successfully")
        
        # Verify tables were created
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f"Current tables in database: {tables}")
        
        return True
        
    except OperationalError as e:
        logger.error(f"Database connection error during initialization: {e}")
        logger.error("Database may not be accessible or configured")
        return False
    except Exception as e:
        logger.error(f"Error during database initialization: {e}", exc_info=True)
        return False


def check_database_health():
    """
    Check if database is healthy and tables exist.
    
    Returns tuple (is_healthy: bool, error_message: str or None)
    """
    from app import db
    
    try:
        # Test connection
        result = db.session.execute(text("SELECT 1"))
        if not result:
            return False, "Database query returned no result"
        
        # Check if critical tables exist
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        critical_tables = ['users', 'students', 'student_records', 'permissions']
        missing = [t for t in critical_tables if t not in existing_tables]
        
        if missing:
            return False, f"Missing tables: {', '.join(missing)}"
        
        logger.debug("✓ Database health check passed")
        return True, None
        
    except OperationalError as e:
        return False, f"Database connection error: {str(e)[:100]}"
    except Exception as e:
        return False, f"Database error: {str(e)[:100]}"


def ensure_database_ready():
    """
    Ensure database is ready before handling requests.
    
    This should be called in before_first_request or before critical operations.
    """
    from app import db
    
    try:
        is_healthy, error = check_database_health()
        
        if is_healthy:
            logger.info("✓ Database is healthy and ready")
            return True
        
        logger.warning(f"Database health check failed: {error}")
        logger.info("Attempting to initialize database...")
        
        if initialize_database():
            logger.info("✓ Database initialized successfully")
            return True
        else:
            logger.error("✗ Database initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"Error in ensure_database_ready: {e}", exc_info=True)
        return False

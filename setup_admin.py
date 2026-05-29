import sys
import logging
from app import create_app, db
from app.models import User
from app.database_init import initialize_database, check_database_health

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

with app.app_context():
    try:
        logger.info("="*60)
        logger.info("INITIALIZING ADMIN USER")
        logger.info("="*60)
        
        # Step 1: Ensure database is initialized
        logger.info("\n[Step 1] Checking database health...")
        is_healthy, error = check_database_health()
        if not is_healthy:
            logger.info(f"  Database not ready: {error}")
            logger.info("  Attempting to initialize tables...")
            if not initialize_database():
                raise Exception("Failed to initialize database tables")
            logger.info("  ✓ Database initialized")
        else:
            logger.info("  ✓ Database is healthy")
        
        # Step 2: Create admin user if needed
        logger.info("\n[Step 2] Setting up admin user...")
        admin_username = "admin"
        admin_password = "admin123"

        existing_admin = User.query.filter_by(username=admin_username, role="admin").first()
        if existing_admin:
            logger.info(f"  ✓ Admin user '{admin_username}' already exists (ID: {existing_admin.id})")
        else:
            logger.info(f"  Creating new admin user '{admin_username}'...")
            admin = User(username=admin_username, role="admin", is_active=True)
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            logger.info(f"  ✓ Admin user '{admin_username}' created successfully (ID: {admin.id})")
        
        # Step 3: Final verification
        logger.info("\n[Step 3] Verifying database setup...")
        is_healthy, error = check_database_health()
        if is_healthy:
            logger.info("  ✓ All checks passed!")
            logger.info("\n" + "="*60)
            logger.info("✓ SETUP COMPLETE - System is ready to use!")
            logger.info("="*60)
            logger.info("\nYou can now:")
            logger.info("  1. Visit the website")
            logger.info("  2. Register as a student")
            logger.info("  3. Log in as admin (username: admin, password: admin123)")
            logger.info("\n")
            sys.exit(0)
        else:
            raise Exception(f"Database health check failed: {error}")
            
    except Exception as e:
        logger.error(f"\n✗ SETUP FAILED: {str(e)}", exc_info=True)
        db.session.rollback()
        sys.exit(1)

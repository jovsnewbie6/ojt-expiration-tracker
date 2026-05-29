import sys
import logging
from app import create_app, db
from app.models import User
from app.database_init import initialize_database, check_database_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()


def create_or_fix_admin():
    """Create admin if missing OR fix existing admin inconsistencies."""

    admin_username = "admin"
    admin_password = "admin123"

    logger.info("\n[Step 2] Checking admin account...")

    # IMPORTANT: do NOT filter by role only
    existing_admin = User.query.filter_by(username=admin_username).first()

    if existing_admin:
        logger.info(f"  Found existing user '{admin_username}' (ID: {existing_admin.id})")

        # FORCE FIX: ensure admin is valid
        existing_admin.role = "admin"
        existing_admin.is_active = True
        existing_admin.set_password(admin_password)

        db.session.commit()

        logger.info("  ✓ Admin account updated and verified")

    else:
        logger.info("  Creating new admin user...")

        admin = User(
            username=admin_username,
            role="admin",
            is_active=True
        )
        admin.set_password(admin_password)

        db.session.add(admin)
        db.session.commit()

        logger.info("  ✓ Admin created successfully")


with app.app_context():
    try:
        logger.info("=" * 60)
        logger.info("INITIALIZING ADMIN SYSTEM")
        logger.info("=" * 60)

        # STEP 1: DB health check
        logger.info("\n[Step 1] Checking database health...")

        is_healthy, error = check_database_health()

        if not is_healthy:
            logger.warning(f"Database not healthy: {error}")
            logger.info("Attempting database initialization...")

            if not initialize_database():
                raise Exception("Database initialization failed")

            logger.info("✓ Database initialized")

        else:
            logger.info("✓ Database is healthy")

        # STEP 2: ADMIN FIX/CREATE
        create_or_fix_admin()

        # STEP 3: FINAL VERIFY
        logger.info("\n[Step 3] Final verification...")

        is_healthy, error = check_database_health()

        if not is_healthy:
            raise Exception(f"Final health check failed: {error}")

        logger.info("================================================")
        logger.info("✓ SYSTEM READY - ADMIN CONFIGURED SUCCESSFULLY")
        logger.info("================================================")

        sys.exit(0)

    except Exception as e:
        logger.error(f"SETUP FAILED: {str(e)}", exc_info=True)
        db.session.rollback()
        sys.exit(1)
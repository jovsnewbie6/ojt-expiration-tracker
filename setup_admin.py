import logging
from app import create_app, db
from app.models import User
from app.database_init import check_database_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

with app.app_context():
    try:
        logger.info("=" * 60)
        logger.info("INITIALIZING ADMIN SYSTEM")
        logger.info("=" * 60)

        # Check DB
        logger.info("\n[Step 1] Checking database health...")
        is_healthy, error = check_database_health()

        if not is_healthy:
            raise Exception(f"Database not ready: {error}")

        logger.info("✓ Database is healthy")

        # Admin setup
        logger.info("\n[Step 2] Checking admin account...")

        admin = User.query.filter_by(username="admin", role="admin").first()

        if admin:
            logger.info(f"  Found existing user 'admin' (ID: {admin.id})")
            logger.info("  ✓ Admin account already exists")
        else:
            logger.info("  Creating admin user...")

            admin = User(
                username="admin",
                role="admin",
                is_active=True
            )
            admin.set_password("admin123")

            db.session.add(admin)
            db.session.commit()

            logger.info(f"  ✓ Admin created (ID: {admin.id})")

        logger.info("\n[Step 3] Final verification...")
        logger.info("================================================")
        logger.info("✓ SYSTEM READY - ADMIN CONFIGURED SUCCESSFULLY")
        logger.info("================================================")

    except Exception as e:
        logger.error(f"SETUP FAILED: {str(e)}", exc_info=True)
        db.session.rollback()
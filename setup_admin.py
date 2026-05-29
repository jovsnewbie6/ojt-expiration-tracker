import sys
import logging
from app import create_app, db
from app.models import User

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

with app.app_context():
    try:
        logger.info("Attempting to initialize admin user...")
        
        # Ensure tables exist
        db.create_all()
        logger.info("Database tables verified")
        
        admin_username = "admin"
        admin_password = "admin123"

        existing_admin = User.query.filter_by(username=admin_username, role="admin").first()
        if existing_admin:
            logger.info(f"Admin user '{admin_username}' already exists (ID: {existing_admin.id})")
            print(f"✓ Admin user '{admin_username}' already exists (ID: {existing_admin.id})")
            sys.exit(0)
        
        admin = User(username=admin_username, role="admin", is_active=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        logger.info(f"Admin user '{admin_username}' created successfully (ID: {admin.id})")
        print(f"✓ Admin user '{admin_username}' created successfully (ID: {admin.id})")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}", exc_info=True)
        print(f"✗ Error creating admin user: {str(e)}", file=sys.stderr)
        db.session.rollback()
        sys.exit(1)

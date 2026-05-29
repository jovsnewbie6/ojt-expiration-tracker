#!/usr/bin/env python
"""
Simulate Render deployment startup to verify system is working.
This tests what happens on first deployment with a fresh database.
"""

import logging
import sys
import os
from pathlib import Path

# Setup logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("SIMULATING RENDER DEPLOYMENT - FIRST STARTUP")
print("="*70)

# Step 1: Check environment
print("\n[1/5] Checking environment configuration...")
from config import Config
try:
    db_url = Config.SQLALCHEMY_DATABASE_URI
    env = Config.ENV
    logger.info(f"✓ Environment: {env}")
    logger.info(f"✓ Database: {db_url.split('/')[-1] if '/' in db_url else 'SQLite'}")
except Exception as e:
    logger.error(f"✗ Environment check failed: {e}")
    sys.exit(1)

# Step 2: Create Flask app
print("\n[2/5] Creating Flask application...")
try:
    from app import create_app, db
    app = create_app()
    logger.info("✓ Flask app created")
except Exception as e:
    logger.error(f"✗ App creation failed: {e}", exc_info=True)
    sys.exit(1)

# Step 3: Check database health
print("\n[3/5] Checking database health...")
with app.app_context():
    try:
        from app.database_init import check_database_health, initialize_database
        
        is_healthy, error = check_database_health()
        if is_healthy:
            logger.info("✓ Database is healthy")
        else:
            logger.warning(f"Database not ready: {error}")
            logger.info("Attempting to initialize...")
            if initialize_database():
                logger.info("✓ Database initialized successfully")
            else:
                raise Exception("Failed to initialize database")
    except Exception as e:
        logger.error(f"✗ Database check failed: {e}", exc_info=True)
        sys.exit(1)

# Step 4: Verify tables exist
print("\n[4/5] Verifying database tables...")
with app.app_context():
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_tables = ['users', 'students', 'student_records', 'permissions']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            logger.warning(f"Missing tables: {missing}")
            logger.info("Attempting to create...")
            from app.database_init import initialize_database
            if not initialize_database():
                raise Exception("Failed to create tables")
        
        logger.info(f"✓ All required tables present: {', '.join(required_tables)}")
    except Exception as e:
        logger.error(f"✗ Table verification failed: {e}", exc_info=True)
        sys.exit(1)

# Step 5: Setup admin user
print("\n[5/5] Setting up admin user...")
with app.app_context():
    try:
        from app.models import User
        admin = User.query.filter_by(username="admin", role="admin").first()
        if admin:
            logger.info(f"✓ Admin user exists (ID: {admin.id})")
        else:
            logger.info("Creating admin user...")
            admin = User(username="admin", role="admin", is_active=True)
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            logger.info(f"✓ Admin user created (ID: {admin.id})")
    except Exception as e:
        logger.error(f"✗ Admin setup failed: {e}", exc_info=True)
        sys.exit(1)

# Final verification
print("\n" + "="*70)
print("SYSTEM STARTUP VERIFICATION - ALL CHECKS PASSED!")
print("="*70)

print("""
✓ Environment configured
✓ Flask app initialized
✓ Database connected
✓ All tables created
✓ Admin user ready

🚀 SYSTEM IS READY FOR USE!

Next steps:
1. Visit the website
2. Click "Register" to create a student account
3. Log in as student with your credentials
4. Use "Forgot Password" to reset password if needed
5. Admin can log in with:
   - Username: admin
   - Password: admin123

""")

sys.exit(0)

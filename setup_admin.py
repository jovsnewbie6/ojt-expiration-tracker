import sys
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    try:
        admin_username = "admin"
        admin_password = "admin123"

        existing_admin = User.query.filter_by(username=admin_username, role="admin").first()
        if existing_admin:
            print(f"✓ Admin user '{admin_username}' already exists (ID: {existing_admin.id})")
            sys.exit(0)
        
        admin = User(username=admin_username, role="admin", is_active=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"✓ Admin user '{admin_username}' created successfully (ID: {admin.id})")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error creating admin user: {str(e)}", file=sys.stderr)
        db.session.rollback()
        sys.exit(1)

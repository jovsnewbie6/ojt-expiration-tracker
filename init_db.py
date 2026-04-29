import os
from app import db, create_app
from app.models import User

def setup_admin():
    # Force the app to use the Render/Neon DATABASE_URL
    app = create_app()
    
    with app.app_context():
        try:
            print("Connecting to Neon...")
            db.create_all()
            
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("Creating admin...")
                new_admin = User(username='admin', role='admin', is_active=True)
                new_admin.set_password('admin123')
                db.session.add(new_admin)
                db.session.commit()
                print("Admin created successfully!")
            else:
                print("Admin already exists.")
        except Exception as e:
            print(f"DATABASE ERROR: {e}")
            # This ensures the build doesn't just hang
            import sys
            sys.exit(1)

if __name__ == "__main__":
    setup_admin()

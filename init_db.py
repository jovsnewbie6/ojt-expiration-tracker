import os
from app import db, create_app
from app.models import User

def setup_admin():
    app = create_app()

    with app.app_context():
        try:
            print("Checking database connection...")

            # ❌ DO NOT create tables here anymore
            # db.create_all()  ← REMOVE THIS

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
            import sys
            sys.exit(1)

if __name__ == "__main__":
    setup_admin()

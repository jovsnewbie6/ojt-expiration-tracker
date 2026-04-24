from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    admin_username = "admin"
    admin_password = "admin123"

    existing_admin = User.query.filter_by(username=admin_username, role="admin").first()
    if existing_admin:
        print("Admin user already exists.")
    else:
        admin = User(username=admin_username, role="admin")
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print("Admin user 'admin' created successfully.")

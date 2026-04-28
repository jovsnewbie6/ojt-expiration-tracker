from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import sys

app = create_app()

with app.app_context():
    try:
        # Find the default admin
        user = Admin.query.filter_by(username='admin').first()
        
        if user:
            # UPDATE THESE TWO LINES
            user.username = 'YourNewUsername' 
            
            # Make sure 'password_hash' matches the column name in your models.py
            user.password_hash = generate_password_hash('YourNewStrongPassword')
            
            db.session.commit()
            print("[+] Admin credentials updated successfully!")
        else:
            print("[-] Error: Could not find a user with the username 'admin'.")
            
    except Exception as e:
        print(f"[-] A database error occurred: {e}")
        db.session.rollback()
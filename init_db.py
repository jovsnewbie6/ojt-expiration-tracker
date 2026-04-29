"""
Database initialization script for Neon PostgreSQL.
Creates all tables and seeds a default admin user.
"""

from app import db, create_app
from app.models import User


def init_database():
    """Initialize the database with tables and default admin user."""
    print("Starting database initialization...")
    
    # Create Flask app instance
    app = create_app()
    print("✓ Flask app created")
    
    # Create all tables within app context
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created")
        
        # Check if admin user already exists
        print("Checking for existing admin user...")
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print("✓ Admin user already exists")
        else:
            print("Creating new admin user...")
            admin = User(
                username='admin',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            print("✓ Admin user object created with password hash")
            
            # Add and commit to database
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user committed to database")
    
    print("\n✓ Database initialization completed successfully!")


if __name__ == '__main__':
    init_database()

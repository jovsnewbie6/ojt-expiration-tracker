import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import text

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
    
    # Handle database connection string compatibility variations
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url # Changed URL to URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.admin_login'

    # Register Blueprints (Adjust names based on your project files)
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User, Student
        if user_id.startswith('admin_'):
            actual_id = int(user_id.split('_')[1])
            return User.query.get(actual_id)
        elif user_id.startswith('student_'):
            actual_id = int(user_id.split('_')[1])
            return Student.query.get(actual_id)
        return None

    # Application Context Configuration (Failsafe for Neon Deployment)
    with app.app_context():
        # Force production tables to build dynamically bypassing out-of-sync Alembic logs
        # Wrapped in try/except to prevent multi-worker race conditions
        try:
            db.create_all()
        except Exception as e:
            db.session.rollback()
            print(f"Table creation bypassed (handled by another worker): {e}")
        
        # Verify and stretch password column lengths to prevent hash truncation crashes
        try:
            db.session.execute(text("ALTER TABLE users ALTER COLUMN password_hash TYPE VARCHAR(256);"))
            db.session.execute(text("ALTER TABLE students ALTER COLUMN password_hash TYPE VARCHAR(256);"))
            
            # ADD THIS LINE to fix the missing username column:
            db.session.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS username VARCHAR(80);"))
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Table alteration bypassed: {e}")

        # Core Permissions Auto-Seeding
        from app.models import Permission
        permissions_list = [
            ('can_deactivate_users', 'Grants power to enable/disable user accounts.'),
            ('can_approve_accounts', 'Allows approving pending student or clerk registrations.'),
            ('can_assign_roles', 'Allows promoting a standard user to moderator or supervisor.'),
            ('can_edit_records', 'Allows modifying existing OJT tracking and expiration details.'),
            ('can_delete_records', 'Bypasses soft-deactivation to permanently delete rows.'),
            ('can_manage_exports', 'Grants permission to upload Excel sheets or download CSV files.'),
            ('can_view_logs', 'Allows viewing history of who modified system data.'),
            ('can_bypass_deadlines', 'Allows manually extending OJT tracking deadlines.')
        ]
        
        try:
            for name, desc in permissions_list:
                if not Permission.query.filter_by(name=name).first():
                    db.session.add(Permission(name=name, description=desc))
            db.session.commit()
        except Exception:
            db.session.rollback()

    return app
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_migrate import Migrate, upgrade # 1. Import Migrate AND upgrade

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate() # 2. Create the migrate object

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
    
    # 1. Handle database connection string
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 2. Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db) # 4. Attach Migrate to the app and db
    login_manager.init_app(app)

    # 3. Handle migrations on startup
    with app.app_context():
        try:
            # This automatically applies your migration files
            upgrade()
        except Exception as e:
            print(f"Database migration failed: {e}")

    # 4. Register Blueprints and User Loader
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

    # 5. Core Permissions Auto-Seeding (Safe to keep)
    with app.app_context():
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
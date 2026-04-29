import os
import logging
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from config import Config

basedir = Path(__file__).resolve().parent.parent

# SQLAlchemy setup - supports both SQLite (development) and Postgres (production)
# Database URL is configured in config.py with automatic postgres:// → postgresql:// conversion
db = SQLAlchemy()
login_manager = LoginManager()


def _ensure_sqlite_columns(app):
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        return

    with db.engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(student_records)"))
        existing_columns = {row[1] for row in result}
        columns_to_add = [
            ("company_name", "VARCHAR(120)", "''"),
            ("business_nature", "VARCHAR(120)", "''"),
            ("validity", "VARCHAR(60)", "''"),
            ("notarized_date", "DATE", "NULL"),
            ("student_count", "INTEGER", "0"),
            ("status", "VARCHAR(30)", "'Pending'"),
            ("has_resume", "INTEGER", "0"),
            ("has_med_cert", "INTEGER", "0"),
            ("has_consent_form", "INTEGER", "0"),
            ("has_moa", "INTEGER", "0"),
            ("has_insurance", "INTEGER", "0"),
            ("has_intent_letter", "INTEGER", "0"),
            ("has_endorsement_letter", "INTEGER", "0"),
            ("year_section", "VARCHAR(60)", "''"),
            ("is_complete", "INTEGER", "0"),
            ("attachments", "TEXT", "'[]'"),
        ]

        for name, type_, default in columns_to_add:
            if name not in existing_columns:
                conn.execute(text(f"ALTER TABLE student_records ADD COLUMN {name} {type_} DEFAULT {default}"))
        conn.commit()


def _create_default_admin_user(app):
    from app.models import User

    admin_username = app.config.get("ADMIN_USER", "admin")
    admin_password = app.config.get("ADMIN_PASSWORD", "admin123")

    if not User.query.filter_by(username=admin_username).first():
        admin = User(username=admin_username, role="admin")
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(Path(__file__).resolve().parent, "templates"),
        static_folder=os.path.join(Path(__file__).resolve().parent, "static"),
    )
    app.config.from_object(config_class)
    
    # Configure logging
    if not app.debug:
        if not app.logger.hasHandlers():
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            app.logger.addHandler(handler)
            app.logger.setLevel(logging.INFO)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login_choice"
    login_manager.login_message = "Please log in to continue."

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User, Student
        
        try:
            # Parse the user type from the ID (format: "admin_1" or "student_1")
            if user_id and isinstance(user_id, str):
                if user_id.startswith("admin_"):
                    user_id_num = int(user_id.split("_")[1])
                    return User.query.get(user_id_num)
                elif user_id.startswith("student_"):
                    user_id_num = int(user_id.split("_")[1])
                    return Student.query.get(user_id_num)
            
            # Fallback for old-style IDs (for backward compatibility)
            try:
                user_id_num = int(user_id) if isinstance(user_id, str) else user_id
                admin = User.query.get(user_id_num)
                if admin:
                    return admin
                student = Student.query.get(user_id_num)
                return student
            except (ValueError, TypeError):
                return None
        except Exception as e:
            app.logger.error(f"Error loading user {user_id}: {str(e)}")
            return None

    with app.app_context():
        from app import models

        try:
            # Create all database tables (works with both SQLite and Postgres)
            db.create_all()
            # Ensure SQLite schema compatibility on development
            _ensure_sqlite_columns(app)
            app.logger.info("Database initialized successfully")
            
            # Initialize default admin user for Render deployment
            try:
                from app.models import User
                
                admin_user = User.query.filter_by(username='admin').first()
                if not admin_user:
                    new_admin = User(username='admin', role='admin', is_active=True)
                    new_admin.set_password('admin123')
                    db.session.add(new_admin)
                    db.session.commit()
                    app.logger.info("Default admin user created successfully")
                else:
                    app.logger.info("Admin user already exists")
            except Exception as e:
                app.logger.error(f"Admin user initialization error: {e}")
                # Don't raise - allow app to continue if admin user initialization fails
                
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")
            raise

    from app.routes import main_bp

    app.register_blueprint(main_bp)
    app.jinja_env.globals["getattr"] = getattr

    return app

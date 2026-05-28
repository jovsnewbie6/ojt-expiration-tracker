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

        result = conn.execute(text("PRAGMA table_info(students)"))
        student_columns = {row[1] for row in result}
        student_columns_to_add = [
            ("role", "VARCHAR(30)", "'student'"),
        ]

        for name, type_, default in student_columns_to_add:
            if name not in student_columns:
                conn.execute(text(f"ALTER TABLE students ADD COLUMN {name} {type_} DEFAULT {default}"))
        conn.commit()


def _fix_email_constraint(app):
    """Remove unique constraint from students.email if it exists (PostgreSQL only)"""
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        return
    
    try:
        # Only attempt to fix if database is already accessible
        with db.engine.connect() as conn:
            try:
                # First check if the students table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'students'
                    )
                """))
                table_exists = result.scalar()
                
                if not table_exists:
                    app.logger.debug("Students table does not exist yet, skipping email constraint fix")
                    return
                
                # Check if the unique constraint exists
                result = conn.execute(text("""
                    SELECT constraint_name FROM information_schema.table_constraints 
                    WHERE table_name='students' AND constraint_type='UNIQUE' 
                    AND constraint_name LIKE '%email%'
                """))
                constraints = result.fetchall()
                
                for constraint in constraints:
                    constraint_name = constraint[0]
                    app.logger.info(f"Dropping unique constraint: {constraint_name}")
                    try:
                        conn.execute(text(f"ALTER TABLE students DROP CONSTRAINT IF EXISTS {constraint_name}"))
                        conn.commit()
                        app.logger.info(f"Successfully dropped constraint: {constraint_name}")
                    except Exception as e:
                        app.logger.debug(f"Could not drop constraint {constraint_name}: {e}")
                        conn.rollback()
            except Exception as e:
                # Table might not exist yet or query failed
                app.logger.debug(f"Could not query constraints: {e}")
                try:
                    conn.rollback()
                except:
                    pass
    except Exception as e:
        app.logger.debug(f"Could not connect to database for constraint fix: {e}")
        # This is not critical - database might not be ready yet, continue anyway


def _create_default_admin_user(app):
    from app.models import User

    admin_username = app.config.get("ADMIN_USER", "admin")
    admin_password = app.config.get("ADMIN_PASSWORD", "admin123")

    if not User.query.filter_by(username=admin_username).first():
        admin = User(username=admin_username, role="admin")
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()


def _seed_core_permissions():
    from app.models import Permission

    core_permissions = [
        ("can_deactivate_users", "Deactivate or reactivate internal user accounts."),
        ("can_approve_accounts", "Approve or reject new account requests."),
        ("can_assign_roles", "Assign roles or manage RBAC permissions for staff."),
        ("can_edit_records", "Edit student records and submission details."),
        ("can_delete_records", "Delete student records from the system."),
        ("can_manage_exports", "Export and manage data reports."),
        ("can_view_logs", "View audit logs and activity reports."),
        ("can_bypass_deadlines", "Bypass expiration deadlines for special cases."),
    ]

    for name, description in core_permissions:
        if not Permission.query.filter_by(name=name).first():
            db.session.add(Permission(name=name, description=description))
    db.session.commit()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app import models  # LOAD MODELS HERE

    with app.app_context():
        db.create_all()

        _seed_core_permissions()
        _create_default_admin_user(app)

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
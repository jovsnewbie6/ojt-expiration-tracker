import os
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from config import Config

basedir = Path(__file__).resolve().parent.parent

db = SQLAlchemy()


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

    db.init_app(app)

    with app.app_context():
        from app import models

        db.create_all()
        _ensure_sqlite_columns(app)
        from app.models import StudentRecord

        unfilled_year_sections = StudentRecord.query.filter(
            (StudentRecord.year_section == "") | (StudentRecord.year_section.is_(None))
        ).all()
        for record in unfilled_year_sections:
            record.year_section = " ".join(
                filter(None, [record.college_year, record.section])
            ).strip()
            record.is_complete = record.has_all_requirements
        if unfilled_year_sections:
            db.session.commit()

        _create_default_admin_user(app)

    from app.routes import main_bp

    app.register_blueprint(main_bp)
    app.jinja_env.globals["getattr"] = getattr

    return app

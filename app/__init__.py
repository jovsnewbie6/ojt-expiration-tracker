import os
import logging
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

from config import Config

# -------------------
# EXTENSIONS (GLOBAL)
# -------------------
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.join(Path(__file__).resolve().parent, "templates"),
        static_folder=os.path.join(Path(__file__).resolve().parent, "static"),
    )

    # -------------------
    # CONFIG
    # -------------------
    app.config.from_object(config_class)

    # -------------------
    # INIT EXTENSIONS
    # -------------------
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "main.login_choice"
    login_manager.login_message = "Please log in to continue."

    # -------------------
    # USER LOADER
    # -------------------
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User, Student

        if not user_id:
            return None

        try:
            # admin_1 or student_1 format
            if isinstance(user_id, str) and user_id.startswith("admin_"):
                return User.query.get(int(user_id.split("_")[1]))

            if isinstance(user_id, str) and user_id.startswith("student_"):
                return Student.query.get(int(user_id.split("_")[1]))

            # fallback (Flask-Login default)
            user = User.query.get(user_id)
            if user:
                return user

            return Student.query.get(user_id)

        except Exception as e:
            app.logger.error(f"user_loader error: {e}")
            return None

    # -------------------
    # IMPORT MODELS (IMPORTANT FOR MIGRATIONS)
    # -------------------
    from app import models  # noqa: F401

    # -------------------
    # BLUEPRINTS
    # -------------------
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # ❌ IMPORTANT: NO db.create_all()
    # ❌ IMPORTANT: NO ensure_database_ready()
@app.before_request
def ensure_tables_exist():
    if not hasattr(app, "tables_checked"):
        try:
            db.create_all()
            app.tables_checked = True
            app.logger.info("Database tables checked/created safely")
        except Exception as e:
            app.logger.error(f"DB init error: {e}")
    # Migration ONLY handles schema

    # -------------------
    # LOGGING
    # -------------------
    log_level = logging.INFO if app.debug else logging.INFO

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    ))

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)

    app.logger.info("Application started successfully")

    return app
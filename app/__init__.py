import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate, upgrade
from config import Config
from sqlalchemy import text # Add this

# Setup logging to see errors without crashing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
    
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.admin_login'

    # Force self-healing database initialization
    with app.app_context():
        try:
            # 1. Ensure all tables exist (the proper way)
            db.create_all() 
            logger.info("Tables checked/created.")

            # 2. Add columns if missing
            columns_to_ensure = [
                ("students", "enrollment_year", "VARCHAR(4)"),
                ("students", "username", "VARCHAR(80)"),
                ("student_records", "has_medical_cert", "BOOLEAN DEFAULT FALSE"),
                ("student_records", "hours_required", "INTEGER DEFAULT 486"),
                ("student_records", "hours_rendered", "INTEGER DEFAULT 0")
            ]
            for table, col, col_type in columns_to_ensure:
                try:
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type};"))
                except Exception:
                    pass 
            db.session.commit()
            logger.info("Database schema synchronized.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Critical Database failure: {e}")

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

    return app
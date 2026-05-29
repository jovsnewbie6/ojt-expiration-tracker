from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Import ALL models
from app.models import User, Student, StudentRecord, Permission
print("Tables in metadata:", db.metadata.tables.keys())

# Register blueprints
from app.routes import main_bp
app.register_blueprint(main_bp)
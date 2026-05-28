from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Import ALL models
import app.models

# Register blueprints
from app.routes import main_bp
app.register_blueprint(main_bp)

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully.")
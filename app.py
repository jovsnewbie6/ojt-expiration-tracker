from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# IMPORT MODELS HERE
from app.models import User, Student, StudentRecord, Permission

with app.app_context():
    db.create_all()
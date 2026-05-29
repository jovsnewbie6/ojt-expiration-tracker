import os
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"

if DOTENV_PATH.exists():
    for line in DOTENV_PATH.read_text().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep:
            os.environ.setdefault(key.strip(), value.strip())


class Config:
    # SECURITY: SECRET_KEY MUST be set in environment for production
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if os.getenv("FLASK_ENV") == "production":
            raise ValueError("SECRET_KEY environment variable is required for production")
        SECRET_KEY = "dev-secret-key-not-for-production"
    
    # Determine if running in production
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV != "production"
    
    # Database URL configuration with Postgres support for Render
    # Falls back to SQLite for local development
    _database_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'moa.db'}")
    
    # Replace postgres:// with postgresql:// for SQLAlchemy 1.4+ compatibility
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder - use temp directory on Render (files deleted on restart)
    # For persistent storage, use Render Disk or external storage
    if os.getenv("RENDER"):
        # Render environment - use writable temporary location
        UPLOAD_FOLDER = "/tmp/uploads"
    else:
        # Local development
        UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # SQLAlchemy connection pool settings for Render PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {}
    if not _database_url.startswith("sqlite:"):
        # PostgreSQL-specific connection pooling settings
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": 5,  # Smaller pool for serverless
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_pre_ping": True,  # Test connection before using it
            "connect_args": {"connect_timeout": 10},
        }
    
    # Logging
    LOG_LEVEL = logging.WARNING if not DEBUG else logging.INFO

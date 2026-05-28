import os
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
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
    
    # Database URL configuration with Postgres support for Render
    # Falls back to SQLite for local development
    _database_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'moa.db'}")
    
    # Replace postgres:// with postgresql:// for SQLAlchemy 1.4+ compatibility
    # This is required for Render and other modern deployments
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ADMIN_USER = os.getenv("ADMIN_USER", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # SQLAlchemy connection pool settings for Render PostgreSQL
    # Only apply to PostgreSQL, not SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {}
    if not _database_url.startswith("sqlite:"):
        # PostgreSQL-specific connection pooling settings
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": 5,  # Smaller pool for serverless
            "pool_recycle": 3600,  # Recycle connections every hour
            "pool_pre_ping": True,  # Test connection before using it
        }

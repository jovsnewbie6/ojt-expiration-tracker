#!/usr/bin/env python3
"""
Create Director Admin Account for PUP MOA Tracking System
=========================================================
This script initializes the Director's admin account in the Neon PostgreSQL database.
Run this script once after deploying to Render.com for the first time.

Usage:
    python create_director.py
    
Environment Variables:
    DATABASE_URL: PostgreSQL connection string (from Render or .env)
    DIRECTOR_USERNAME: Director's login username (default: 'director')
    DIRECTOR_PASSWORD: Director's login password (default: 'ChangeMe@2024')
    SECRET_KEY: Flask secret key (from .env or environment)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app, db
from app.models import User


def create_director_account():
    """Create the Director's admin account in the database."""
    
    # Initialize the Flask app with current config
    app = create_app()
    
    with app.app_context():
        try:
            # Get credentials from environment or use defaults
            director_username = os.getenv("DIRECTOR_USERNAME", "director")
            director_password = os.getenv("DIRECTOR_PASSWORD", "ChangeMe@2024")
            
            # Check if director already exists
            existing_director = User.query.filter_by(username=director_username).first()
            
            if existing_director:
                print(f"✓ Director account '{director_username}' already exists (ID: {existing_director.id})")
                print(f"  Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
                return True
            
            # Create new Director account
            director = User(
                username=director_username,
                role="admin",  # "admin" role grants full access
                is_active=True
            )
            director.set_password(director_password)
            
            # Add to database
            db.session.add(director)
            db.session.commit()
            
            print("=" * 70)
            print("✓ Director Admin Account Created Successfully!")
            print("=" * 70)
            print(f"Username:  {director_username}")
            print(f"Role:      Admin (Full System Access)")
            print(f"User ID:   {director.id}")
            print(f"Database:  {app.config['SQLALCHEMY_DATABASE_URI']}")
            print("=" * 70)
            print("\nNEXT STEPS:")
            print("1. Log in to https://<your-render-app>/admin/login")
            print(f"   Username: {director_username}")
            print(f"   Password: {director_password}")
            print("2. Change the password immediately after first login")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"✗ Error creating Director account: {e}", file=sys.stderr)
            db.session.rollback()
            return False


if __name__ == "__main__":
    print("PUP MOA Tracking System - Director Account Initialization")
    print("-" * 70)
    
    try:
        success = create_director_account()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"✗ Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

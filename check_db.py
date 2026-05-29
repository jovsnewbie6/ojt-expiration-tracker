#!/usr/bin/env python
"""Quick database verification script"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        tables = [row[0] for row in result.fetchall()]
        
        print("\n✓ Database Tables Created:")
        for table in tables:
            print(f"  ✓ {table}")
        
        print(f"\nTotal: {len(tables)} tables")
        
        # Verify critical tables
        required_tables = ['permissions', 'users', 'students', 'student_records', 'user_permissions', 'student_permissions']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            print(f"\n✗ Missing tables: {missing}")
        else:
            print(f"\n✓ All required tables present!")
            
    except Exception as e:
        print(f"✗ Error checking tables: {e}")

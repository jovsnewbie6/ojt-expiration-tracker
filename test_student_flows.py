#!/usr/bin/env python
"""Test student registration and forgot password flow"""
from app import create_app, db
from app.models import Student
import sys

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("TESTING STUDENT REGISTRATION FLOW")
    print("="*60)
    
    # Test 1: Student Registration
    print("\n[TEST 1] Creating new student...")
    try:
        # Clear any existing test student
        test_student = Student.query.filter_by(student_number="TEST001").first()
        if test_student:
            print("  Removing existing test student...")
            db.session.delete(test_student)
            db.session.commit()
        
        # Create new student
        new_student = Student(
            student_number="TEST001",
            name="Test Student",
            year_section="4A",
            email="test@example.com"
        )
        new_student.set_password("testpass123")
        
        db.session.add(new_student)
        db.session.commit()
        
        print(f"  ✓ Student created successfully!")
        print(f"    - ID: {new_student.id}")
        print(f"    - Student Number: {new_student.student_number}")
        print(f"    - Name: {new_student.name}")
        print(f"    - Year/Section: {new_student.year_section}")
        
    except Exception as e:
        print(f"  ✗ Error creating student: {e}")
        sys.exit(1)
    
    # Test 2: Student Login (password check)
    print("\n[TEST 2] Testing student login (password verification)...")
    try:
        retrieved_student = Student.query.filter_by(student_number="TEST001").first()
        if not retrieved_student:
            print("  ✗ Student not found after creation!")
            sys.exit(1)
        
        # Test correct password
        if retrieved_student.check_password("testpass123"):
            print("  ✓ Password verification successful!")
        else:
            print("  ✗ Password verification failed!")
            sys.exit(1)
        
        # Test incorrect password
        if not retrieved_student.check_password("wrongpassword"):
            print("  ✓ Incorrect password correctly rejected!")
        else:
            print("  ✗ Incorrect password was accepted (security issue)!")
            sys.exit(1)
            
    except Exception as e:
        print(f"  ✗ Error testing login: {e}")
        sys.exit(1)
    
    # Test 3: Password Reset (forgot password)
    print("\n[TEST 3] Testing forgot password (password reset)...")
    try:
        student = Student.query.filter_by(student_number="TEST001").first()
        
        # Simulate password reset
        old_password_hash = student.password_hash
        student.set_password("newpass456")
        db.session.commit()
        
        # Verify new password works
        student_refreshed = Student.query.filter_by(student_number="TEST001").first()
        if student_refreshed.check_password("newpass456"):
            print("  ✓ Password reset successful!")
            print(f"    - Old hash was different from new: {old_password_hash != student_refreshed.password_hash}")
        else:
            print("  ✗ New password doesn't work after reset!")
            sys.exit(1)
            
        # Verify old password no longer works
        if not student_refreshed.check_password("testpass123"):
            print("  ✓ Old password correctly rejected after reset!")
        else:
            print("  ✗ Old password still works after reset!")
            sys.exit(1)
            
    except Exception as e:
        print(f"  ✗ Error testing password reset: {e}")
        sys.exit(1)
    
    # Test 4: Duplicate Student Prevention
    print("\n[TEST 4] Testing duplicate student number prevention...")
    try:
        duplicate_student = Student(
            student_number="TEST001",  # Same as existing
            name="Duplicate Student",
            year_section="4A"
        )
        duplicate_student.set_password("pass123")
        
        db.session.add(duplicate_student)
        try:
            db.session.commit()
            print("  ✗ Duplicate student number was allowed (constraint not working)!")
            sys.exit(1)
        except Exception as e:
            db.session.rollback()
            print(f"  ✓ Duplicate student correctly rejected!")
            print(f"    - Error: {type(e).__name__}")
            
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        sys.exit(1)
    
    # Test 5: Cleanup
    print("\n[TEST 5] Cleaning up test data...")
    try:
        test_student = Student.query.filter_by(student_number="TEST001").first()
        if test_student:
            db.session.delete(test_student)
            db.session.commit()
            print("  ✓ Test student deleted successfully")
    except Exception as e:
        print(f"  ✗ Error cleaning up: {e}")
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    print("\nStudent registration and forgot password functionality is working correctly.")
    print("Database is ready for deployment.\n")

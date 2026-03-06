#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive debug script for AI Invigilator
Tests all components and login flow
"""
import sys
import os

# Set encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("AI INVIGILATOR - COMPREHENSIVE DEBUG")
print("=" * 70)

# Step 1: Test imports
print("\n[1/8] Testing imports...")
try:
    from flask import Flask, session
    from flask_wtf.csrf import CSRFProtect
    print("    [OK] Flask and extensions")
except Exception as e:
    print(f"    [ERROR] Flask import: {e}")
    sys.exit(1)

try:
    from database import db, Invigilator, Student
    print("    [OK] Database models")
except Exception as e:
    print(f"    [ERROR] Database import: {e}")
    sys.exit(1)

try:
    from config import Config, get_config
    print("    [OK] Configuration")
except Exception as e:
    print(f"    [ERROR] Config import: {e}")
    sys.exit(1)

# Step 2: Initialize app
print("\n[2/8] Initializing Flask app...")
try:
    from app import app
    print("    [OK] Flask app created")
except Exception as e:
    print(f"    [ERROR] App initialization: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Check database connection
print("\n[3/8] Checking database connection...")
with app.app_context():
    try:
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1'))
        print("    [OK] Database connected")
        uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')
        print(f"    [INFO] URI: {uri[:30]}...")
    except Exception as e:
        print(f"    [ERROR] Database connection: {e}")
        sys.exit(1)

# Step 4: Check CSRF configuration
print("\n[4/8] Checking CSRF configuration...")
with app.app_context():
    try:
        secret_key = app.config.get('SECRET_KEY')
        if secret_key and secret_key != 'dev-secret-key-change-in-production':
            print("    [OK] SECRET_KEY configured")
        else:
            print("    [WARNING] Using default SECRET_KEY")
        
        # Check if CSRF is initialized
        from flask_wtf.csrf import CSRFProtect
        print("    [OK] CSRF available")
    except Exception as e:
        print(f"    [ERROR] CSRF config: {e}")

# Step 5: Check invigilator accounts
print("\n[5/8] Checking invigilator accounts...")
with app.app_context():
    try:
        invigilators = Invigilator.query.all()
        print(f"    [INFO] Found {len(invigilators)} invigilator(s)")
        for inv in invigilators:
            print(f"      - ID={inv.id}, Email={inv.email}, Active={inv.is_active}")
    except Exception as e:
        print(f"    [ERROR] Query invigilators: {e}")

# Step 6: Test login route exists
print("\n[6/8] Checking login route...")
with app.app_context():
    try:
        rules = [str(r) for r in app.url_map.iter_rules()]
        if '/login/<role>' in rules or any('login' in r for r in rules):
            print("    [OK] Login route registered")
        else:
            print("    [WARNING] Login route not found!")
    except Exception as e:
        print(f"    [ERROR] Route check: {e}")

# Step 7: Test session management
print("\n[7/8] Testing session management...")
with app.app_context():
    try:
        from auth.authentication import SessionManager
        print("    [OK] SessionManager imported")
        
        # Test session creation
        test_session = SessionManager.create_session('test', 'invigilator')
        print("    [OK] Session creation works")
    except Exception as e:
        print(f"    [ERROR] Session management: {e}")

# Step 8: Check login function
print("\n[8/8] Checking login function...")
with app.app_context():
    try:
        # Check if login route handler exists
        from app import login
        print("    [OK] Login function exists")
        
        # Check the source code for the bug
        import inspect
        source = inspect.getsource(login)
        if "SessionManager.create_session(str(user.id), user.id)" in source:
            print("    [ERROR] BUG FOUND: Line 206 still has 'user.id' instead of 'invigilator'")
        elif "SessionManager.create_session(str(user.id), 'invigilator')" in source:
            print("    [OK] Login function has correct role parameter")
        else:
            print("    [INFO] Login function source checked")
    except Exception as e:
        print(f"    [ERROR] Login function check: {e}")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Run: python app.py")
print("2. Visit: http://localhost:5000/login/invigilator")
print("3. Login with: johndoe@gmail.com / password123")
print("\nIf login still fails, check browser console (F12) for errors.")

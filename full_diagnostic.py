#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE DIAGNOSTIC - CHECK EVERYTHING
"""
import sys
import os
import socket
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("COMPREHENSIVE SYSTEM DIAGNOSTIC")
print("=" * 80)

# 1. Check Python and environment
print("\n[1/15] Python Environment")
print(f"    Python version: {sys.version}")
print(f"    Python executable: {sys.executable}")
print(f"    Current directory: {os.getcwd()}")
print(f"    Script directory: {os.path.dirname(os.path.abspath(__file__))}")

# 2. Check .env file
print("\n[2/15] Environment Configuration")
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    print(f"    .env file: EXISTS at {env_path}")
    from dotenv import load_dotenv
    load_dotenv()
    print(f"    SECRET_KEY set: {bool(os.environ.get('SECRET_KEY'))}")
    print(f"    DATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT SET')[:50]}")
    print(f"    FLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT SET')}")
else:
    print(f"    .env file: MISSING at {env_path}")

# 3. Check port 5000
print("\n[3/15] Port 5000 Availability")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', 5000))
if result == 0:
    print(f"    Port 5000: IN USE by another process")
else:
    print(f"    Port 5000: FREE")
sock.close()

# 4. Check PostgreSQL
print("\n[4/15] PostgreSQL Connection")
db_url = os.environ.get('DATABASE_URL', '')
if 'postgresql' in db_url:
    print(f"    Database type: PostgreSQL")
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        print(f"    Connection: SUCCESS")
        conn.close()
    except Exception as e:
        print(f"    Connection: FAILED - {str(e)[:100]}")
else:
    print(f"    Database type: SQLite (no connection test needed)")

# 5. Test all critical imports
print("\n[5/15] Critical Module Imports")
imports_to_test = [
    ('Flask', 'flask', 'Flask'),
    ('Flask-WTF', 'flask_wtf', 'CSRFProtect'),
    ('SQLAlchemy', 'sqlalchemy', 'create_engine'),
    ('MediaPipe', 'mediapipe', 'solutions'),
    ('OpenCV', 'cv2', 'imread'),
    ('Pandas', 'pandas', 'DataFrame'),
    ('NumPy', 'numpy', 'array'),
    ('PyJWT', 'jwt', 'encode'),
    ('bcrypt', 'bcrypt', 'hashpw'),
]

for name, module, attr in imports_to_test:
    try:
        mod = __import__(module, fromlist=[attr])
        getattr(mod, attr)
        print(f"    [OK] {name}")
    except Exception as e:
        print(f"    [FAIL] {name}: {str(e)[:50]}")

# 6. Test database models import
print("\n[6/15] Database Models")
try:
    from database import db, Invigilator, Student, Admin
    print(f"    [OK] Database models imported")
    print(f"    Invigilator table: {Invigilator.__tablename__}")
except Exception as e:
    print(f"    [FAIL] {type(e).__name__}: {str(e)[:100]}")

# 7. Test Flask app creation
print("\n[7/15] Flask App Creation")
try:
    from app import app
    print(f"    [OK] Flask app created")
    print(f"    Secret key set: {bool(app.config.get('SECRET_KEY'))}")
    print(f"    Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')[:50]}")
except Exception as e:
    print(f"    [FAIL] {type(e).__name__}: {str(e)[:100]}")
    import traceback
    traceback.print_exc()

# 8. Test database connection via app
print("\n[8/15] Database Connection (via app)")
try:
    from app import app
    with app.app_context():
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1'))
        print(f"    [OK] Database query successful")
except Exception as e:
    print(f"    [FAIL] {type(e).__name__}: {str(e)[:100]}")

# 9. Test route registration
print("\n[9/15] Route Registration")
try:
    from app import app
    routes = [str(r) for r in app.url_map.iter_rules()]
    login_routes = [r for r in routes if 'login' in r.lower()]
    print(f"    Total routes: {len(routes)}")
    print(f"    Login routes: {login_routes}")
    if '/login/<role>' in routes:
        print(f"    [OK] Invigilator login route registered")
    else:
        print(f"    [WARN] Login route not found")
except Exception as e:
    print(f"    [FAIL] {type(e).__name__}: {str(e)[:100]}")

# 10. Test template files
print("\n[10/15] Template Files")
templates = [
    'templates/login.html',
    'templates/admin_login.html',
    'templates/invigilator_dashboard.html',
    'templates/admin_dashboard.html',
    'templates/base.html'
]
for tmpl in templates:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), tmpl)
    if os.path.exists(path):
        print(f"    [OK] {tmpl}")
    else:
        print(f"    [MISSING] {tmpl}")

# 11. Test CSRF token generation
print("\n[11/15] CSRF Token Generation")
try:
    from app import app, csrf_token
    with app.test_request_context():
        token = csrf_token()
        print(f"    [OK] CSRF token generated: {token[:20]}...")
except Exception as e:
    print(f"    [FAIL] {type(e).__name__}: {str(e)[:100]}")

# 12. Test session management
print("\n[12/15] Session Management")
try:
    from auth.authentication import SessionManager
    from flask import session
    with app.test_request_context():
        SessionManager.create_session('test', 'invigilator')
        print(f"    [OK] Session created")
except Exception as e:
    print(f"    [FAIL] {type(e).__name__}: {str(e)[:100]}")

# 13. Test login functionality
print("\n[13/15] Login Functionality (Test Client)")
try:
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        resp = client.get('/login/invigilator')
        print(f"    GET /login/invigilator: Status {resp.status_code}")
        if resp.status_code == 200:
            html = resp.get_data(as_text=True)
            if 'csrf_token' in html:
                print(f"    [OK] CSRF token in page")
            else:
                print(f"    [WARN] No CSRF token in page")
        else:
            print(f"    [FAIL] Status {resp.status_code}")
except Exception as e:
    print(f"    [FAIL] {type(e).__name__}: {str(e)[:100]}")

# 14. Check file permissions
print("\n[14/15] File Permissions")
try:
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_write.tmp')
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print(f"    [OK] Write permissions OK")
except Exception as e:
    print(f"    [FAIL] Cannot write: {str(e)[:100]}")

# 15. Check for common issues
print("\n[15/15] Common Issues Check")
issues = []

# Check if app.run is in correct place
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if content.count('app.run(') > 1:
        issues.append("Multiple app.run() calls found")
    if 'if __name__' in content:
        main_block = content.split('if __name__')[1]
        if 'app.run(' not in main_block:
            issues.append("app.run() is outside if __name__ block")

# Check CSRF
if '@app.template_global(\'csrf_token\')' not in content:
    issues.append("csrf_token() template global missing")

# Check CSP
with open('templates/base.html', 'r', encoding='utf-8') as f:
    base_content = f.read()
    if 'Content-Security-Policy' not in base_content:
        issues.append("CSP meta tag missing")

if issues:
    for issue in issues:
        print(f"    [ISSUE] {issue}")
else:
    print(f"    [OK] No common issues found")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)

# Summary
print("\nRECOMMENDATIONS:")
if 'PostgreSQL' in db_url:
    print("  - If PostgreSQL connection fails, try SQLite temporarily")
    print("    Change DATABASE_URL in .env to: sqlite:///ai_invigilator.db")
print("  - Run: python app.py 2>&1 to see all errors")
print("  - Check Windows Event Viewer if app crashes silently")
print("  - Try: netstat -an | findstr :5000 to see if port is in use")
print("=" * 80)

#!/usr/bin/env python
"""
Check all dependencies required by app.py
Run: python check_deps.py
"""
import sys
import importlib

# All imports from app.py and related modules
DEPENDENCIES = [
    # Core Flask
    ('flask', 'Flask'),
    ('flask_wtf.csrf', 'CSRFProtect'),
    ('flask_limiter', 'Limiter'),
    ('flask_migrate', 'Migrate'),
    ('flask_sqlalchemy', 'SQLAlchemy'),
    ('flask_mail', 'Mail'),
    
    # Database
    ('sqlalchemy', 'SQLAlchemy'),
    ('psycopg', 'psycopg'),  # PostgreSQL
    
    # Data/Utilities
    ('pandas', 'pd'),
    ('pytz', 'timezone'),
    ('numpy', 'numpy'),
    ('openpyxl', 'openpyxl'),  # Excel support
    
    # Authentication/Security
    ('jwt', 'PyJWT'),
    ('bcrypt', 'bcrypt'),
    ('werkzeug.security', 'generate_password_hash'),
    
    # Computer Vision / AI
    ('mediapipe', 'mediapipe'),
    ('cv2', 'cv2'),  # OpenCV
    ('PIL', 'Image'),  # Pillow
    
    # Email
    ('flask_mail', 'Mail'),
    
    # SMS
    ('africastalking', 'africastalking'),  # Optional
    
    # Code execution
    ('requests', 'requests'),
    
    # Other
    ('dotenv', 'load_dotenv'),
    ('datetime', 'datetime'),
    ('json', 'json'),
    ('os', 'os'),
    ('threading', 'threading'),
]

print("=" * 70)
print("DEPENDENCY CHECK FOR AI INVIGILATOR")
print("=" * 70)

installed = 0
missing = []
optional_missing = []

for module, name in DEPENDENCIES:
    try:
        importlib.import_module(module)
        print(f"[OK] {module}")
        installed += 1
    except ImportError as e:
        # Mark some as optional
        if module in ['africastalking']:
            print(f"[OPTIONAL] {module} - SMS functionality will be disabled")
            optional_missing.append(module)
        else:
            print(f"[MISSING] {module} - {e}")
            missing.append(module)

print("\n" + "=" * 70)
print(f"INSTALLED: {installed}/{len(DEPENDENCIES)}")
print(f"MISSING: {len(missing)}")
print(f"OPTIONAL MISSING: {len(optional_missing)}")
print("=" * 70)

if missing:
    print("\n[ERROR] Missing required dependencies!")
    print("\nTo install all missing packages, run:")
    print(f"    pip install {' '.join(missing)}")
    sys.exit(1)
else:
    print("\n[SUCCESS] All required dependencies are installed!")
    if optional_missing:
        print(f"\nNote: Optional packages missing: {', '.join(optional_missing)}")
    sys.exit(0)

#!/usr/bin/env python3

print("Starting import test...")

try:
    from flask import Flask
    print("✓ Flask imported")
except ImportError as e:
    print(f"✗ Flask import failed: {e}")

try:
    from config import get_config
    print("✓ Config imported")
except ImportError as e:
    print(f"✗ Config import failed: {e}")

try:
    from database import db
    print("✓ Database imported")
except ImportError as e:
    print(f"✗ Database import failed: {e}")

try:
    app = Flask(__name__)
    print("✓ Flask app created")
except Exception as e:
    print(f"✗ Flask app creation failed: {e}")

print("Import test complete")
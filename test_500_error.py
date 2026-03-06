#!/usr/bin/env python
# Test login and capture the actual error
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app
from database import db

print("=" * 70)
print("TESTING LOGIN - CAPTURING 500 ERROR")
print("=" * 70)

with app.test_client() as client:
    # Enable exception propagation to see the actual error
    app.config['TESTING'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    print("\n[1] Testing Admin Login...")
    try:
        resp = client.get('/admin/login')
        print(f"    GET Status: {resp.status_code}")
        
        # Get CSRF token
        html = resp.get_data(as_text=True)
        import re
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        # Try to login
        login_data = {'email': 'admin@test.com', 'password': 'admin123'}
        if csrf_token:
            login_data['csrf_token'] = csrf_token
            
        resp = client.post('/admin/login', data=login_data, follow_redirects=False)
        print(f"    POST Status: {resp.status_code}")
        
        if resp.status_code == 500:
            print("    [ERROR] 500 Internal Server Error!")
            # Try to get the error
            try:
                resp = client.post('/admin/login', data=login_data)
            except Exception as e:
                print(f"    Exception: {type(e).__name__}: {e}")
        elif resp.status_code in [301, 302]:
            print(f"    [OK] Redirect to: {resp.location}")
        else:
            print(f"    [INFO] Response: {resp.status_code}")
            
    except Exception as e:
        print(f"    [EXCEPTION] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n[2] Testing Invigilator Login...")
    try:
        resp = client.get('/login/invigilator')
        print(f"    GET Status: {resp.status_code}")
        
        # Get CSRF token
        html = resp.get_data(as_text=True)
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        # Try to login
        login_data = {'email': 'johndoe@gmail.com', 'password': 'password123'}
        if csrf_token:
            login_data['csrf_token'] = csrf_token
            
        resp = client.post('/login/invigilator', data=login_data, follow_redirects=False)
        print(f"    POST Status: {resp.status_code}")
        
        if resp.status_code == 500:
            print("    [ERROR] 500 Internal Server Error!")
        elif resp.status_code in [301, 302]:
            print(f"    [OK] Redirect to: {resp.location}")
        else:
            print(f"    [INFO] Response: {resp.status_code}")
            
    except Exception as e:
        print(f"    [EXCEPTION] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)

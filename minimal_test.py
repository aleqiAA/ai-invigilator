#!/usr/bin/env python
# Minimal test to find the 500 error cause
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import app

# Force error display
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['DEBUG'] = True

print("Testing login routes...")

with app.test_client() as client:
    print("\n1. GET /login/invigilator")
    try:
        resp = client.get('/login/invigilator')
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   Data: {resp.get_data(as_text=True)[:500]}")
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")
    
    print("\n2. GET /admin/login")
    try:
        resp = client.get('/admin/login')
        print(f"   Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"   Data: {resp.get_data(as_text=True)[:500]}")
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")
    
    print("\n3. POST /login/invigilator (valid creds)")
    try:
        # First get the page to extract CSRF
        resp = client.get('/login/invigilator')
        html = resp.get_data(as_text=True)
        
        import re
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        csrf_token = csrf_match.group(1) if csrf_match else None
        print(f"   CSRF Token: {csrf_token[:20] if csrf_token else 'NONE'}...")
        
        # Try login
        resp = client.post('/login/invigilator', 
                          data={'email': 'johndoe@gmail.com', 'password': 'password123', 'csrf_token': csrf_token},
                          follow_redirects=False)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 302:
            print(f"   Redirect: {resp.location}")
        elif resp.status_code == 500:
            print(f"   500 ERROR!")
            print(f"   Response: {resp.get_data(as_text=True)[:1000]}")
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("\nDone!")

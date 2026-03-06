#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test login functionality
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app
from database import db, Invigilator
from auth.authentication import SessionManager
from flask import session as flask_session

print("Testing login flow...")

with app.test_client() as client:
    # Test 1: GET login page
    print("\n[1] GET /login/invigilator")
    resp = client.get('/login/invigilator')
    print(f"    Status: {resp.status_code}")
    print(f"    Content-Type: {resp.content_type}")
    
    # Check if CSRF token is in the page
    html = resp.get_data(as_text=True)
    if 'csrf_token' in html:
        print("    [OK] CSRF token found in page")
    else:
        print("    [ERROR] CSRF token NOT found in page")
    
    # Extract CSRF token from the HTML
    import re
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    csrf_token = csrf_match.group(1) if csrf_match else None
    print(f"    CSRF Token: {csrf_token[:20] + '...' if csrf_token else 'NOT FOUND'}")
    
    # Test 2: POST login with correct credentials
    print("\n[2] POST /login/invigilator (valid credentials)")
    login_data = {
        'email': 'johndoe@gmail.com',
        'password': 'password123'
    }
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    resp = client.post('/login/invigilator', data=login_data, follow_redirects=False)
    print(f"    Status: {resp.status_code}")
    print(f"    Location: {resp.location if resp.status_code in [301, 302] else 'N/A'}")
    
    # Check session
    with client.session_transaction() as sess:
        print(f"    Session role: {sess.get('role', 'NOT SET')}")
        print(f"    Session user_id: {sess.get('user_id', 'NOT SET')}")
        print(f"    Session name: {sess.get('name', 'NOT SET')}")
        
        if sess.get('role') == 'invigilator':
            print("    [OK] Login successful - role is 'invigilator'")
        else:
            print("    [ERROR] Login failed - role is not 'invigilator'")
    
    # Test 3: POST login with wrong password
    print("\n[3] POST /login/invigilator (wrong password)")
    login_data = {
        'email': 'johndoe@gmail.com',
        'password': 'wrongpassword'
    }
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    resp = client.post('/login/invigilator', data=login_data, follow_redirects=False)
    print(f"    Status: {resp.status_code}")
    
    if resp.status_code == 200:
        html = resp.get_data(as_text=True)
        if 'Invalid credentials' in html:
            print("    [OK] Correctly rejected wrong password")
        else:
            print("    [INFO] Login page returned (expected)")
    
    print("\n" + "=" * 60)
    print("LOGIN TEST COMPLETE")
    print("=" * 60)

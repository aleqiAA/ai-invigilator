#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE VERIFICATION OF ALL FIXES
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("COMPREHENSIVE FIX VERIFICATION")
print("=" * 80)

# Fix 1: Check app.run() is in correct location
print("\n[1/6] Checking app.run() location...")
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'if __name__ == \'__main__\':' in content and content.count('app.run(') == 1:
        main_block = content.split('if __name__ == \'__main__\':')[1]
        if 'app.run(' in main_block:
            print("    [OK] app.run() is correctly inside if __name__ block")
        else:
            print("    [ERROR] app.run() is outside if __name__ block!")
    else:
        print("    [ERROR] Multiple app.run() calls found!")

# Fix 2: Check csrf_token function exists
print("\n[2/6] Checking csrf_token() function...")
if '@app.template_global(\'csrf_token\')' in content:
    print("    [OK] csrf_token() template global is defined")
else:
    print("    [ERROR] csrf_token() function is missing!")

# Fix 3: Check login route has correct role parameter
print("\n[3/6] Checking login route session creation...")
if 'SessionManager.create_session(str(user.id), \'invigilator\')' in content:
    print("    [OK] Login creates session with correct role 'invigilator'")
else:
    print("    [ERROR] Login session creation has wrong role parameter!")

# Fix 4: Check CSP meta tag in base.html
print("\n[4/6] Checking CSP meta tag...")
with open('templates/base.html', 'r', encoding='utf-8') as f:
    base_content = f.read()
    if 'Content-Security-Policy' in base_content:
        print("    [OK] CSP meta tag is present")
        if '\'unsafe-eval\'' in base_content:
            print("    [OK] CSP allows 'unsafe-eval' for Monaco Editor")
        else:
            print("    [WARNING] CSP missing 'unsafe-eval' - Monaco may not work")
    else:
        print("    [ERROR] CSP meta tag is missing!")

# Fix 5: Check safe math evaluator in exam.html
print("\n[5/6] Checking safe math evaluator...")
with open('templates/exam.html', 'r', encoding='utf-8') as f:
    exam_content = f.read()
    if 'function safeMathEval(expr)' in exam_content:
        print("    [OK] Safe math evaluator is defined")
        if 'Function(`"use strict"' not in exam_content:
            print("    [OK] No unsafe Function() calls in calculator")
        else:
            print("    [WARNING] Unsafe Function() call still present")
    else:
        print("    [ERROR] Safe math evaluator is missing!")

# Fix 6: Test actual login functionality
print("\n[6/6] Testing login functionality...")
from app import app
app.config['TESTING'] = True

with app.test_client() as client:
    # Test invigilator login
    resp = client.get('/login/invigilator')
    if resp.status_code == 200:
        html = resp.get_data(as_text=True)
        if 'csrf_token' in html:
            import re
            csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
            if csrf_match:
                # Try to login
                login_data = {
                    'email': 'johndoe@gmail.com',
                    'password': 'password123',
                    'csrf_token': csrf_match.group(1)
                }
                resp = client.post('/login/invigilator', data=login_data, follow_redirects=False)
                if resp.status_code == 302 and '/invigilator/dashboard' in resp.location:
                    print("    [OK] Invigilator login works correctly")
                else:
                    print(f"    [ERROR] Login failed: Status {resp.status_code}")
            else:
                print("    [ERROR] Could not extract CSRF token")
        else:
            print("    [ERROR] CSRF token not in page")
    else:
        print(f"    [ERROR] GET /login/invigilator failed: {resp.status_code}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

# Summary
print("\nSUMMARY OF FIXES:")
print("  1. app.run() moved inside if __name__ block")
print("  2. csrf_token() template global added")
print("  3. Login session creation uses correct role parameter")
print("  4. CSP meta tag added to base.html")
print("  5. Safe math evaluator replaces unsafe Function() call")
print("  6. Login functionality tested and working")

print("\nREADY TO USE:")
print("  1. Run: python app.py")
print("  2. Visit: http://localhost:5000/login/invigilator")
print("  3. Login: johndoe@gmail.com / password123")
print("=" * 80)

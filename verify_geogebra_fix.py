#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify GeoGebra Iframe Fix
Checks that all required changes are in place
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("GEOGEBRA IFRAME FIX VERIFICATION")
print("=" * 80)

checks_passed = 0
checks_failed = 0

def check(description, condition, details=""):
    global checks_passed, checks_failed
    if condition:
        print(f"✓ {description}")
        if details:
            print(f"  {details}")
        checks_passed += 1
    else:
        print(f"✗ {description}")
        if details:
            print(f"  {details}")
        checks_failed += 1

# 1. Check manage_questions.html
print("\n[1/4] manage_questions.html Iframe")
try:
    with open('templates/manage_questions.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    check("Iframe src without ?lang=en", 
          'src="https://www.geogebra.org/classic"' in content and '?lang=en' not in content,
          "Removed language parameter")
    
    check("allow attribute present", 
          'allow="fullscreen; clipboard-read; clipboard-write"' in content,
          "Grants fullscreen and clipboard access")
    
    check("referrerpolicy attribute present", 
          'referrerpolicy="no-referrer-when-downgrade"' in content,
          "Secure referrer handling")
    
    check("loading=lazy attribute present", 
          'loading="lazy"' in content,
          "Performance optimization")
    
    check("allowfullscreen attribute present", 
          'allowfullscreen' in content,
          "Allows fullscreen mode")
    
except Exception as e:
    check("manage_questions.html file", False, str(e))

# 2. Check exam.html
print("\n[2/4] exam.html Iframe")
try:
    with open('templates/exam.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    check("Iframe src without ?lang=en", 
          'src="https://www.geogebra.org/classic"' in content and '?lang=en' not in content,
          "Removed language parameter")
    
    check("allow attribute present", 
          'allow="fullscreen; clipboard-read; clipboard-write"' in content,
          "Grants fullscreen and clipboard access")
    
    check("referrerpolicy attribute present", 
          'referrerpolicy="no-referrer-when-downgrade"' in content,
          "Secure referrer handling")
    
except Exception as e:
    check("exam.html file", False, str(e))

# 3. Check app.py CSP headers
print("\n[3/4] app.py CSP Headers")
try:
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    check("Content-Security-Policy header set", 
          'Content-Security-Policy' in content,
          "CSP header added to responses")
    
    check("frame-src includes geogebra.org", 
          'frame-src' in content and 'geogebra.org' in content,
          "Allows GeoGebra iframe embedding")
    
    check("ngrok-skip-browser-warning header", 
          'ngrok-skip-browser-warning' in content,
          "Prevents ngrok browser warnings")
    
except Exception as e:
    check("app.py file", False, str(e))

# 4. Check base.html CSP meta tag
print("\n[4/4] base.html CSP Meta Tag")
try:
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    check("CSP meta tag present", 
          'Content-Security-Policy' in content,
          "Meta tag in HTML head")
    
    check("frame-src directive present", 
          'frame-src' in content,
          "Allows iframe sources")
    
    check("geogebra.org in frame-src", 
          'geogebra.org' in content,
          "GeoGebra domain allowed")
    
except Exception as e:
    check("base.html file", False, str(e))

# Summary
print("\n" + "=" * 80)
print(f"VERIFICATION COMPLETE: {checks_passed} passed, {checks_failed} failed")
print("=" * 80)

if checks_failed > 0:
    print("\n⚠️  Some checks failed. Please review the items above.")
else:
    print("\n✅ All GeoGebra iframe fixes are in place!")
    print("\nNext steps:")
    print("  1. Restart Flask app: python app.py")
    print("  2. Open test page: test_geogebra.html")
    print("  3. Visit: http://localhost:5000/manage_questions/TestExam")
    print("  4. Select 'Graph Sketching (GeoGebra)' - should load correctly")

print("=" * 80)

#!/usr/bin/env python
"""
Add a debug route to app.py for diagnosing login issues
Run this once to add the route, then access /debug_login in browser
"""

# Check if the debug route already exists
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

if '@app.route("/debug_login")' in content:
    print("Debug route already exists!")
else:
    # Find a good place to insert the route - after the imports section
    insert_marker = "app.run(debug=False, host='0.0.0.0', threaded=True)"
    
    debug_route = '''
@app.route('/debug_login')
def debug_login():
    """Debug route to check login status"""
    from flask import session
    return jsonify({
        'session': dict(session),
        'logged_in': 'user_id' in session,
        'role': session.get('role'),
        'user_id': session.get('user_id'),
        'name': session.get('name'),
    })

'''
    
    if insert_marker in content:
        content = content.replace(insert_marker, debug_route + insert_marker)
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Debug route added! Restart the app and visit /debug_login")
    else:
        print("Could not find insertion point. Manual edit required.")

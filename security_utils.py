import os
import re
from werkzeug.utils import secure_filename
from functools import wraps
from flask import abort, request
import hashlib

class SecurityUtils:
    """Security utilities for data protection"""
    
    @staticmethod
    def allowed_file(filename, allowed_extensions):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    @staticmethod
    def secure_upload(file, upload_folder, allowed_extensions):
        """Securely handle file uploads"""
        if not file or file.filename == '':
            return None, "No file selected"
        
        if not SecurityUtils.allowed_file(file.filename, allowed_extensions):
            return None, f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
        
        # Secure filename and add hash to prevent overwrites
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        hash_suffix = hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]
        filename = f"{name}_{hash_suffix}{ext}"
        
        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        return filename, None
    
    @staticmethod
    def sanitize_input(text, max_length=1000):
        """Sanitize user input to prevent XSS"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]*>', '', str(text))
        
        # Limit length
        text = text[:max_length]
        
        # Remove potentially dangerous characters
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        return text.strip()
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_student_id(student_id):
        """Validate student ID format"""
        pattern = r'^STU\d{3,6}$'
        return re.match(pattern, student_id) is not None
    
    @staticmethod
    def hash_file(filepath):
        """Generate SHA256 hash of file for integrity check"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

def require_role(role):
    """Decorator to require specific user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session
            if 'role' not in session or session['role'] != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_csrf():
    """Simple CSRF token validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session
            if request.method == 'POST':
                token = request.form.get('csrf_token')
                if not token or token != session.get('csrf_token'):
                    abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

import os
import re
import hashlib
import hmac
import time
from werkzeug.utils import secure_filename
from functools import wraps
from flask import abort, request, session, jsonify

# ─────────────────────────────────────────────────────────────────────────────
# Known datacenter/VM/cloud IP ranges (simplified - extend as needed)
# These suggest the student may be running in a virtual environment
# ─────────────────────────────────────────────────────────────────────────────
SUSPICIOUS_USER_AGENTS = [
    'headlesschrome', 'phantomjs', 'selenium', 'webdriver',
    'puppeteer', 'playwright', 'bot', 'crawler', 'python-requests',
    'curl/', 'wget/'
]

# Suspicious request headers that automated tools often send
AUTOMATION_HEADERS = [
    'x-selenium-driver',
    'x-webdriver',
    'x-playwright',
]


class SecurityUtils:
    """Security utilities for data protection and anti-tampering"""

    # ── File Upload ───────────────────────────────────────────────────────

    @staticmethod
    def allowed_file(filename, allowed_extensions):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def secure_upload(file, upload_folder, allowed_extensions):
        if not file or file.filename == '':
            return None, "No file selected"

        if not SecurityUtils.allowed_file(file.filename, allowed_extensions):
            return None, f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"

        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        hash_suffix = hashlib.md5(str(os.urandom(16)).encode()).hexdigest()[:8]
        filename = f"{name}_{hash_suffix}{ext}"

        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        return filename, None

    # ── Input Sanitization ────────────────────────────────────────────────

    @staticmethod
    def sanitize_input(text, max_length=1000):
        if not text:
            return ""
        text = re.sub(r'<[^>]*>', '', str(text))
        text = text[:max_length]
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        return text.strip()

    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_student_id(student_id):
        pattern = r'^[A-Za-z0-9_-]{3,20}$'
        return re.match(pattern, student_id) is not None

    @staticmethod
    def hash_file(filepath):
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    # ── Request Fingerprinting ────────────────────────────────────────────

    @staticmethod
    def get_request_fingerprint():
        """
        Creates a fingerprint of the current request for session binding.
        Used to detect if a session token is being used from a different device.
        """
        components = [
            request.headers.get('User-Agent', ''),
            request.headers.get('Accept-Language', ''),
            request.headers.get('Accept-Encoding', ''),
        ]
        raw = '|'.join(components)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    @staticmethod
    def is_automated_request():
        """
        Detect if the request comes from an automated tool (Selenium, Playwright etc.)
        Returns (is_automated: bool, reason: str)
        """
        user_agent = request.headers.get('User-Agent', '').lower()

        # Check for headless/automation user agents
        for suspicious in SUSPICIOUS_USER_AGENTS:
            if suspicious in user_agent:
                return True, f"Suspicious user agent: {suspicious}"

        # Check for automation-specific headers
        for header in AUTOMATION_HEADERS:
            if request.headers.get(header):
                return True, f"Automation header detected: {header}"

        # Check for missing headers that real browsers always send
        if not request.headers.get('Accept'):
            return True, "Missing Accept header"

        if not request.headers.get('User-Agent'):
            return True, "Missing User-Agent header"

        return False, None

    # ── Session Integrity ─────────────────────────────────────────────────

    @staticmethod
    def bind_session_to_device():
        """
        Store a device fingerprint in the session when exam starts.
        Call this from /start_exam.
        """
        session['device_fingerprint'] = SecurityUtils.get_request_fingerprint()
        session['exam_start_ip'] = request.remote_addr

    @staticmethod
    def verify_session_device():
        """
        Verify the current request matches the device that started the exam.
        Returns (is_valid: bool, reason: str)
        Call this on sensitive exam endpoints like /submit_answer.
        """
        stored_fp = session.get('device_fingerprint')
        if not stored_fp:
            return True, None  # No fingerprint stored — allow (exam not started yet)

        current_fp = SecurityUtils.get_request_fingerprint()
        if current_fp != stored_fp:
            return False, "Device fingerprint mismatch — possible session hijack"

        # Warn (but don't block) on IP change — mobile networks can change IP
        stored_ip = session.get('exam_start_ip')
        if stored_ip and stored_ip != request.remote_addr:
            # Log this but don't fail — IP changes are common on mobile
            print(f"[Security] IP changed during exam: {stored_ip} → {request.remote_addr}")

        return True, None


# ─────────────────────────────────────────────────────────────────────────────
# Decorators
# ─────────────────────────────────────────────────────────────────────────────

def require_role(role):
    """Decorator to require specific user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def block_automation(f):
    """
    Decorator to block automated/headless browser requests on exam endpoints.
    Apply to /start_exam, /submit_answer, /end_exam.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_automated, reason = SecurityUtils.is_automated_request()
        if is_automated:
            print(f"[Security] Blocked automated request: {reason} | IP: {request.remote_addr}")
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        return f(*args, **kwargs)
    return decorated_function


def verify_exam_device(f):
    """
    Decorator to verify the request comes from the same device that started the exam.
    Apply to /submit_answer and other exam session endpoints.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_valid, reason = SecurityUtils.verify_session_device()
        if not is_valid:
            print(f"[Security] Device mismatch: {reason} | IP: {request.remote_addr}")
            return jsonify({'success': False, 'message': 'Session security violation detected'}), 403
        return f(*args, **kwargs)
    return decorated_function


def validate_csrf(f):
    """CSRF token validation decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or \
                    request.headers.get('X-CSRF-Token')
            if not token or not hmac.compare_digest(
                str(token), str(session.get('csrf_token', ''))
            ):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Security Implementation Guide

## Implemented Security Features

### 1. **File Upload Security**
- Max file size: 16MB
- Allowed extensions: png, jpg, jpeg, csv
- Secure filename sanitization
- Hash-based unique filenames
- File integrity verification (SHA256)

**Usage:**
```python
from security_utils import SecurityUtils

filename, error = SecurityUtils.secure_upload(
    file, 
    app.config['UPLOAD_FOLDER'], 
    app.config['ALLOWED_EXTENSIONS']
)
```

### 2. **Input Sanitization**
- XSS prevention
- HTML tag removal
- Length limits
- Special character escaping

**Usage:**
```python
clean_text = SecurityUtils.sanitize_input(user_input, max_length=1000)
```

### 3. **Data Encryption**
- Fernet symmetric encryption
- Encrypt sensitive data (phone numbers, emails)
- File encryption support

**Usage:**
```python
from encryption import encryption

# Encrypt data
encrypted = encryption.encrypt("sensitive data")

# Decrypt data
decrypted = encryption.decrypt(encrypted)
```

### 4. **Password Security**
- Bcrypt hashing (12 rounds)
- Already implemented in database.py

### 5. **Session Security**
- HTTPOnly cookies (prevents XSS)
- Secure flag (HTTPS only)
- SameSite=Lax (CSRF protection)
- 1-hour timeout

### 6. **Rate Limiting**
- Already implemented in app.py
- 100 requests per hour default
- 5 login attempts per minute

### 7. **Role-Based Access Control**
**Usage:**
```python
from security_utils import require_role

@app.route('/admin')
@require_role('invigilator')
def admin_page():
    return "Admin only"
```

### 8. **CSRF Protection**
**Usage:**
```python
from security_utils import validate_csrf

@app.route('/submit', methods=['POST'])
@validate_csrf()
def submit_form():
    # Process form
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install cryptography
```

### 2. Generate Encryption Key
Run the app once to generate a key, then add to `.env`:
```
ENCRYPTION_KEY=your-generated-key-here
```

### 3. Update app.py
Add these imports:
```python
from security_utils import SecurityUtils, require_role
from encryption import encryption
```

### 4. Secure File Uploads
Replace file upload code with:
```python
filename, error = SecurityUtils.secure_upload(
    request.files['file'],
    app.config['UPLOAD_FOLDER'],
    app.config['ALLOWED_EXTENSIONS']
)
if error:
    return jsonify({'error': error}), 400
```

### 5. Encrypt Sensitive Data
Before saving to database:
```python
student.phone_number = encryption.encrypt(phone_number)
```

When retrieving:
```python
phone = encryption.decrypt(student.phone_number)
```

## Additional Recommendations

### For Production:
1. **Use HTTPS** - Enable SSL/TLS certificates
2. **PostgreSQL** - Switch from SQLite
3. **Environment Variables** - Never commit secrets
4. **Backup Encryption** - Encrypt database backups
5. **Audit Logging** - Log all sensitive operations
6. **2FA** - Add two-factor authentication
7. **IP Whitelisting** - Restrict admin access
8. **Regular Updates** - Keep dependencies updated

### Database Security:
```python
# Use parameterized queries (already done with SQLAlchemy)
# Never use string concatenation for SQL

# Good (SQLAlchemy ORM)
Student.query.filter_by(email=email).first()

# Bad (vulnerable to SQL injection)
# db.execute(f"SELECT * FROM students WHERE email='{email}'")
```

### API Security:
```python
# Add API key authentication
@app.before_request
def check_api_key():
    if request.path.startswith('/api/'):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('API_KEY'):
            abort(401)
```

## Compliance
- **GDPR**: Data encryption, right to deletion
- **FERPA**: Student data protection
- **SOC 2**: Audit trails, access controls

## Testing Security
```bash
# Test file upload limits
curl -X POST -F "file=@large_file.jpg" http://localhost:5000/upload

# Test rate limiting
for i in {1..10}; do curl http://localhost:5000/login; done

# Test XSS prevention
curl -X POST -d "name=<script>alert('xss')</script>" http://localhost:5000/submit
```

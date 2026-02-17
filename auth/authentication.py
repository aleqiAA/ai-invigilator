import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session
import os
from config import Config

class PasswordManager:
    @staticmethod
    def hash_password(password):
        """Hash a password with a random salt."""
        return generate_password_hash(password)
    
    @staticmethod
    def verify_password(hashed_password, password):
        """Verify a password against its hash."""
        return check_password_hash(hashed_password, password)
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength."""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors

class SessionManager:
    @staticmethod
    def create_session(user_id, role, remember_me=False):
        """Create a user session."""
        session['user_id'] = user_id
        session['role'] = role
        session['logged_in'] = True
        
        if remember_me:
            # Extend session lifetime if remember_me is True
            session.permanent = True
    
    @staticmethod
    def destroy_session():
        """Destroy the current session."""
        session.pop('user_id', None)
        session.pop('role', None)
        session.pop('logged_in', None)

class AuthenticationManager:
    def __init__(self):
        self.secret_key = os.environ.get('SECRET_KEY') or Config.SECRET_KEY
    
    def generate_token(self, user_id, role, additional_claims=None):
        """Generate a JWT token."""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
            'iat': datetime.utcnow()
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        """Verify a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_token(self, token):
        """Refresh an existing token."""
        payload = self.verify_token(token)
        if payload:
            # Generate a new token with extended expiration
            new_payload = {
                'user_id': payload['user_id'],
                'role': payload['role'],
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow()
            }
            return jwt.encode(new_payload, self.secret_key, algorithm='HS256')
        return None
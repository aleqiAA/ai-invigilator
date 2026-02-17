import logging
from flask import Blueprint, request, jsonify, session
from marshmallow import ValidationError
from datetime import datetime
from utils.validators import StudentRegistrationSchema
from utils.error_handlers import (
    AuthenticationError, ValidationError as ValidationErr,
    ResourceNotFoundError, DatabaseError
)
from auth.authentication import (
    AuthenticationManager, SessionManager, PasswordManager
)
from database.models import db, User, AuditLog
import uuid

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize authentication manager
auth_manager = AuthenticationManager()
registration_schema = StudentRegistrationSchema()

# ==================== AUTHENTICATION ROUTES ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new student account."""
    try:
        # Validate input
        data = request.get_json()
        if not data:
            raise ValidationErr('No JSON data provided')
        
        validated_data = registration_schema.load(data)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=validated_data['email']).first()
        if existing_user:
            logger.warning(f'Registration attempt with existing email: {validated_data["email"]}')
            raise ValidationErr('Email already registered', details={'email': 'This email is already in use'})
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = PasswordManager.hash_password(validated_data['password'])
        
        new_user = User(
            id=user_id,
            email=validated_data['email'],
            password_hash=password_hash,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone'),
            role='student',
            is_active=True
        )
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        # Create audit log
        AuditLog.log_action(
            user_id=user_id,
            action='USER_REGISTERED',
            resource_type='User',
            resource_id=user_id,
            ip_address=request.remote_addr
        )
        
        logger.info(f'New user registered: {validated_data["email"]}')
        
        return jsonify({
            'message': 'Registration successful',
            'user_id': user_id,
            'email': validated_data['email']
        }), 201
    
    except ValidationError as e:
        logger.error(f'Registration validation error: {e.messages}')
        raise ValidationErr(message='Validation failed', details=e.messages)
    except Exception as e:
        logger.error(f'Registration error: {str(e)}')
        db.session.rollback()
        raise DatabaseError(f'Registration failed: {str(e)}')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and create session."""
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            raise ValidationErr('Email and password required')
        
        email = data['email'].strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            logger.warning(f'Login attempt with non-existent email: {email}')
            raise AuthenticationError('Invalid email or password')
        
        # Verify password
        if not PasswordManager.verify_password(user.password_hash, password):
            logger.warning(f'Failed login attempt for user: {email}')
            raise AuthenticationError('Invalid email or password')
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f'Login attempt for inactive user: {email}')
            raise AuthenticationError('Account is inactive')
        
        # Create session
        SessionManager.create_session(user.id, user.role, remember_me=data.get('remember_me', False))
        
        # Generate token
        token = auth_manager.generate_token(user.id, user.role)
        
        # Log audit
        AuditLog.log_action(
            user_id=user.id,
            action='USER_LOGIN',
            ip_address=request.remote_addr
        )
        
        logger.info(f'User logged in: {email}')
        
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'token': token
        }), 200
    
    except (AuthenticationError, ValidationErr) as e:
        raise e
    except Exception as e:
        logger.error(f'Login error: {str(e)}')
        raise DatabaseError('Login failed')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user and destroy session."""
    try:
        user_id = session.get('user_id')
        
        # Log audit
        if user_id:
            AuditLog.log_action(
                user_id=user_id,
                action='USER_LOGOUT',
                ip_address=request.remote_addr
            )
        
        # Destroy session
        SessionManager.destroy_session()
        
        logger.info(f'User logged out: {user_id}')
        
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        logger.error(f'Logout error: {str(e)}')
        raise

@auth_bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    """Refresh JWT token."""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise AuthenticationError('Missing authorization header')
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        new_token = auth_manager.refresh_token(token)
        
        if not new_token:
            raise AuthenticationError('Invalid or expired token')
        
        return jsonify({
            'message': 'Token refreshed',
            'token': new_token
        }), 200
    except Exception as e:
        logger.error(f'Token refresh error: {str(e)}')
        raise

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            raise AuthenticationError('Not authenticated')
        
        data = request.get_json()
        if not data or not all(k in data for k in ['old_password', 'new_password', 'confirm_password']):
            raise ValidationErr('Old password, new password, and confirm password required')
        
        # Validate new password strength
        is_strong, errors = PasswordManager.validate_password_strength(data['new_password'])
        if not is_strong:
            raise ValidationErr('Password does not meet strength requirements', details={'errors': errors})
        
        if data['new_password'] != data['confirm_password']:
            raise ValidationErr('Passwords do not match')
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            raise ResourceNotFoundError('User', user_id)
        
        # Verify old password
        if not PasswordManager.verify_password(user.password_hash, data['old_password']):
            raise AuthenticationError('Invalid old password')
        
        # Update password
        user.password_hash = PasswordManager.hash_password(data['new_password'])
        db.session.commit()
        
        # Log audit
        AuditLog.log_action(
            user_id=user_id,
            action='PASSWORD_CHANGED',
            ip_address=request.remote_addr
        )
        
        logger.info(f'Password changed for user: {user_id}')
        
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        logger.error(f'Change password error: {str(e)}')
        db.session.rollback()
        raise

@auth_bp.route('/password-reset-request', methods=['POST'])
def password_reset_request():
    """Request password reset."""
    try:
        data = request.get_json()
        if not data or not data.get('email'):
            raise ValidationErr('Email required')
        
        email = data['email'].strip()
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists
            logger.info(f'Password reset requested for non-existent email: {email}')
            return jsonify({'message': 'If email exists, reset link will be sent'}), 200
        
        # Generate reset token
        reset_token = auth_manager.generate_token(
            user.id,
            user.role,
            additional_claims={'purpose': 'password_reset'}
        )
        
        # In production, send email with reset link
        logger.info(f'Password reset requested for: {email}')
        
        # TODO: Send email with reset token
        
        return jsonify({'message': 'If email exists, reset link will be sent'}), 200
    except Exception as e:
        logger.error(f'Password reset request error: {str(e)}')
        raise

# ==================== ERROR HANDLERS ====================

@auth_bp.errorhandler(ValidationErr)
def handle_validation_error(error):
    """Handle validation errors."""
    return jsonify({
        'error': 'Validation Error',
        'message': error.message,
        'details': error.details
    }), error.status_code

@auth_bp.errorhandler(AuthenticationError)
def handle_auth_error(error):
    """Handle authentication errors."""
    return jsonify({
        'error': 'Authentication Error',
        'message': error.message
    }), error.status_code

@auth_bp.errorhandler(DatabaseError)
def handle_db_error(error):
    """Handle database errors."""
    return jsonify({
        'error': 'Database Error',
        'message': error.message
    }), error.status_code
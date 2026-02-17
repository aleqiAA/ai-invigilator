from flask import jsonify
import logging
from functools import wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom exception classes
class AuthenticationError(Exception):
    def __init__(self, message="Authentication failed"):
        self.message = message
        self.status_code = 401
        super().__init__(self.message)

class AuthorizationError(Exception):
    def __init__(self, message="Authorization failed"):
        self.message = message
        self.status_code = 403
        super().__init__(self.message)

class ValidationError(Exception):
    def __init__(self, message="Validation failed", details=None):
        self.message = message
        self.details = details or {}
        self.status_code = 422
        super().__init__(self.message)

class ResourceNotFoundError(Exception):
    def __init__(self, resource_type, resource_id):
        self.message = f"{resource_type} with ID {resource_id} not found"
        self.status_code = 404
        super().__init__(self.message)

class ExamError(Exception):
    def __init__(self, message="Exam operation failed"):
        self.message = message
        self.status_code = 400
        super().__init__(self.message)

class DatabaseError(Exception):
    def __init__(self, message="Database operation failed"):
        self.message = message
        self.status_code = 500
        super().__init__(self.message)

class ExternalServiceError(Exception):
    def __init__(self, service_name, message="External service operation failed"):
        self.service_name = service_name
        self.message = f"{service_name} service: {message}"
        self.status_code = 502
        super().__init__(self.message)

class FileUploadError(Exception):
    def __init__(self, message="File upload failed"):
        self.message = message
        self.status_code = 400
        super().__init__(self.message)

def register_error_handlers(app):
    """Register error handlers with the Flask app."""
    
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        logger.error(f"Authentication error: {error.message}")
        return jsonify({
            'error': 'Authentication Error',
            'message': error.message
        }), error.status_code
    
    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        logger.error(f"Authorization error: {error.message}")
        return jsonify({
            'error': 'Authorization Error',
            'message': error.message
        }), error.status_code
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        logger.error(f"Validation error: {error.message}, details: {error.details}")
        return jsonify({
            'error': 'Validation Error',
            'message': error.message,
            'details': error.details
        }), error.status_code
    
    @app.errorhandler(ResourceNotFoundError)
    def handle_resource_not_found_error(error):
        logger.error(f"Resource not found: {error.message}")
        return jsonify({
            'error': 'Resource Not Found',
            'message': error.message
        }), error.status_code
    
    @app.errorhandler(ExamError)
    def handle_exam_error(error):
        logger.error(f"Exam error: {error.message}")
        return jsonify({
            'error': 'Exam Error',
            'message': error.message
        }), error.status_code
    
    @app.errorhandler(DatabaseError)
    def handle_database_error(error):
        logger.error(f"Database error: {error.message}")
        return jsonify({
            'error': 'Database Error',
            'message': error.message
        }), error.status_code
    
    @app.errorhandler(ExternalServiceError)
    def handle_external_service_error(error):
        logger.error(f"External service error: {error.message}")
        return jsonify({
            'error': 'External Service Error',
            'message': error.message
        }), error.status_code
    
    @app.errorhandler(FileUploadError)
    def handle_file_upload_error(error):
        logger.error(f"File upload error: {error.message}")
        return jsonify({
            'error': 'File Upload Error',
            'message': error.message
        }), error.status_code
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500

def retry(max_attempts=3, delay=1, backoff=2):
    """Decorator to retry a function with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"Attempt {attempts} failed for {func.__name__}: {str(e)}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator

def safe_execute(func, default_return=None, log_error=True):
    """Safely execute a function, returning a default value if it fails."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_error:
                logger.error(f"Error in {func.__name__}: {str(e)}")
            return default_return
    return wrapper
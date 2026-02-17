import os
from datetime import timedelta
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Secret key for sessions and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    # PostgreSQL for production, SQLite for local development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ai_invigilator.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL-specific connection pool settings (ignored by SQLite)
    # These optimize database connection management in production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),  # Number of connections to keep open
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),  # Extra connections allowed beyond pool_size
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),  # Seconds to wait for connection
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 1800)),  # Recycle connections after 30 minutes
        'pool_pre_ping': True,  # Verify connection before using (handles dropped connections)
    }

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL') or 'memory://'

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Security settings
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'dev-salt-change-in-production'

    # Tab switch threshold
    TAB_SWITCH_THRESHOLD = int(os.environ.get('TAB_SWITCH_THRESHOLD') or 3)

    # Camera settings
    CAMERA_INDEX = int(os.environ.get('CAMERA_INDEX') or 0)

    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Alert thresholds
    ALERT_LOW = 'low'
    ALERT_MEDIUM = 'medium'
    ALERT_HIGH = 'high'
    ALERT_CRITICAL = 'critical'

    # File paths
    STUDENT_PHOTOS_PATH = os.environ.get('STUDENT_PHOTOS_PATH') or 'student_photos'

    # SMS Configuration (Africa's Talking)
    AFRICASTALKING_API_KEY = os.environ.get('AFRICASTALKING_API_KEY')
    AFRICASTALKING_USERNAME = os.environ.get('AFRICASTALKING_USERNAME', 'sandbox')
    AFRICASTALKING_SENDER_ID = os.environ.get('AFRICASTALKING_SENDER_ID', 'AI_INVIGILATOR')

    @staticmethod
    def init_app(app):
        # Configure logging
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')

            file_handler = RotatingFileHandler('logs/ai_invigilator.log', maxBytes=10240000, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info('AI Invigilator startup')
            app.logger.info(f'Database URI configured: {app.config["SQLALCHEMY_DATABASE_URI"][:20]}...')


class DevelopmentConfig(Config):
    """Development configuration - uses SQLite by default"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///ai_invigilator.db'
    SQLALCHEMY_ENGINE_OPTIONS = {}  # SQLite doesn't need pool settings
    RATELIMIT_STORAGE_URL = 'memory://'
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration - requires PostgreSQL"""
    DEBUG = False
    # In production, DATABASE_URL must be set (e.g., from Railway/Render)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production-specific pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 1800)),
        'pool_pre_ping': True,
    }
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production security checks
        if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
            app.logger.error('WARNING: Using default SECRET_KEY! Set a secure key in production.')
        
        if not app.config['SQLALCHEMY_DATABASE_URI']:
            app.logger.error('ERROR: DATABASE_URL not set! Application will fail.')
        
        # Log production environment
        app.logger.info('Running in PRODUCTION mode')


class TestingConfig(Config):
    """Testing configuration - uses in-memory SQLite"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration class based on FLASK_ENV environment variable"""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])

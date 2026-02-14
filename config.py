import os
import secrets

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///invigilator.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Stripe
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    
    # Africa's Talk SMS API (Kenya)
    AFRICASTALKING_API_KEY = os.environ.get('AFRICASTALKING_API_KEY', 'your-api-key-here')
    AFRICASTALKING_USERNAME = os.environ.get('AFRICASTALKING_USERNAME', 'sandbox')
    AFRICASTALKING_SENDER_ID = os.environ.get('AFRICASTALKING_SENDER_ID', 'OUK')
    
    # Monitoring thresholds
    MAX_FACE_AWAY_TIME = 5  # seconds
    MAX_NO_FACE_TIME = 3  # seconds
    MAX_MULTIPLE_FACES_TIME = 2  # seconds
    AUDIO_THRESHOLD = 0.5  # voice detection sensitivity
    
    # Paths
    STUDENT_PHOTOS_PATH = 'student_photos'
    EXAM_RECORDINGS_PATH = 'exam_recordings'
    
    # Alert levels
    ALERT_LOW = 'low'
    ALERT_MEDIUM = 'medium'
    ALERT_HIGH = 'high'
    ALERT_CRITICAL = 'critical'

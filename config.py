import os
from datetime import timedelta

class Config:
    """Base application configuration"""
    
    # Get SECRET_KEY from environment, use default if not set (will warn in production)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
    
    # Database configuration
    # DigitalOcean App Platform and other clouds inject DATABASE_URL starting with postgres://
    # SQLAlchemy 1.4+ deprecated it in favor of postgresql://
    _db_url = os.environ.get('DATABASE_URL')
    if _db_url and _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = _db_url or (
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'database.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload configuration
    UPLOAD_FOLDER = 'static/images'
    QR_FOLDER = 'static/qr'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Admin credentials with defaults
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'demo')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'demo')

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Email Configuration (for OTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@hostelmanagement.com')

    # SMS Configuration (Optional - Twilio)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # QR Code Configuration
    BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')

    # OTP Configuration
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
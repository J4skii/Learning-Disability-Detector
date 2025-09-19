"""
Configuration management for LD Detector application.
Handles environment-specific settings and security configurations.
"""
import os
from typing import Optional


class Config:
    """Base configuration class."""
    
    # Security
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: Optional[int] = 3600  # 1 hour
    
    # Database
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL') or 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Mail configuration
    MAIL_SERVER: str = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT: int = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: Optional[str] = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD: Optional[str] = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER: Optional[str] = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME: int = 3600  # 1 hour
    SESSION_COOKIE_SECURE: bool = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    
    # Application settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # Security headers
    SECURITY_PASSWORD_SALT: str = os.environ.get('SECURITY_PASSWORD_SALT') or 'salt-change-in-production'
    
    @staticmethod
    def validate_config() -> list[str]:
        """Validate critical configuration settings."""
        warnings = []
        
        if Config.SECRET_KEY == 'dev-key-change-in-production':
            warnings.append('SECRET_KEY is using default value. Change in production!')
        
        if Config.SECURITY_PASSWORD_SALT == 'salt-change-in-production':
            warnings.append('SECURITY_PASSWORD_SALT is using default value. Change in production!')
        
        if not Config.MAIL_USERNAME:
            warnings.append('MAIL_USERNAME not set. Email functionality will be limited.')
        
        return warnings


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG: bool = True
    TESTING: bool = False
    SESSION_COOKIE_SECURE: bool = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG: bool = False
    TESTING: bool = False
    SESSION_COOKIE_SECURE: bool = True  # Requires HTTPS
    
    @staticmethod
    def validate_production_config() -> list[str]:
        """Validate production-specific settings."""
        warnings = []
        
        if not os.environ.get('SECRET_KEY'):
            warnings.append('SECRET_KEY must be set in production')
        
        if not os.environ.get('SECURITY_PASSWORD_SALT'):
            warnings.append('SECURITY_PASSWORD_SALT must be set in production')
        
        if not os.environ.get('DATABASE_URL'):
            warnings.append('DATABASE_URL should be set in production')
        
        return warnings


class TestingConfig(Config):
    """Testing configuration."""
    TESTING: bool = True
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED: bool = False
    SECRET_KEY: str = 'test-secret-key'


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'default')
    return config_map.get(env, config_map['default'])

"""
Utility functions for LD Detector application.
Handles security, validation, and common operations.
"""
import re
import logging
from typing import Optional, Dict, Any
from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash
from models import User, db


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityValidator:
    """Security validation utilities."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        Returns (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        return True, ""
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate name format."""
        if not name or len(name.strip()) < 2:
            return False
        # Allow letters, spaces, hyphens, and apostrophes
        pattern = r"^[a-zA-Z\s\-']+$"
        return bool(re.match(pattern, name.strip()))
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input to prevent XSS."""
        if not text:
            return ""
        # Remove potentially dangerous characters
        return text.strip()
    
    @staticmethod
    def validate_configuration(config: Dict[str, Any]) -> list[str]:
        """
        Validate application configuration for security issues.
        Returns list of configuration issues found.
        """
        issues = []
        
        # Check secret key
        secret_key = config.get('SECRET_KEY', '')
        if not secret_key or secret_key == 'devkey':
            issues.append("SECRET_KEY is not set or using default value")
        
        # Check database URL
        db_url = config.get('SQLALCHEMY_DATABASE_URI', '')
        if not db_url:
            issues.append("SQLALCHEMY_DATABASE_URI is not set")
        
        # Check session security settings
        if not config.get('SESSION_COOKIE_SECURE', False):
            issues.append("SESSION_COOKIE_SECURE should be True in production")
        
        if not config.get('SESSION_COOKIE_HTTPONLY', True):
            issues.append("SESSION_COOKIE_HTTPONLY should be True")
        
        return issues


class UserManager:
    """User management utilities."""
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """Safely get current user from session."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return None
            
            return db.session.get(User, user_id)
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    @staticmethod
    def create_secure_user(name: str, email: str, password: str, **kwargs) -> tuple[bool, str, Optional[User]]:
        """
        Create a user with security validation.
        Returns (success, message, user_object)
        """
        try:
            # Validate inputs
            if not SecurityValidator.validate_name(name):
                return False, "Invalid name format", None
            
            if not SecurityValidator.validate_email(email):
                return False, "Invalid email format", None
            
            is_valid_password, password_error = SecurityValidator.validate_password(password)
            if not is_valid_password:
                return False, password_error, None
            
            # Sanitize inputs
            name = SecurityValidator.sanitize_input(name)
            email = SecurityValidator.sanitize_input(email).lower()
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                return False, "Email already registered", None
            
            # Create user
            user = User(
                name=name,
                email=email,
                **kwargs
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"User created successfully: {email}")
            return True, "User created successfully", user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            return False, "An error occurred during user creation", None


def login_required(f):
    """Enhanced login required decorator with better error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        # Verify user still exists
        user = UserManager.get_current_user()
        if not user:
            session.clear()
            flash('Session expired. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Enhanced admin required decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))

        user = UserManager.get_current_user()
        if not user or user.role not in ['admin', 'superuser']:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('landing'))

        return f(*args, **kwargs)
    return decorated_function


def counselor_required(f):
    """Enhanced counselor required decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))

        user = UserManager.get_current_user()
        if not user or user.role not in ['counselor', 'admin', 'superuser']:
            flash('Access denied. Counselor or Admin privileges required.', 'error')
            return redirect(url_for('landing'))

        return f(*args, **kwargs)
    return decorated_function


def handle_errors(f):
    """Decorator for consistent error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {e}")
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('index'))
    return decorated_function


def validate_form_data(form_data: Dict[str, Any], required_fields: list) -> tuple[bool, str]:
    """
    Validate form data for required fields and basic security.
    Returns (is_valid, error_message)
    """
    for field in required_fields:
        if not form_data.get(field):
            return False, f"{field.replace('_', ' ').title()} is required."
    
    # Basic XSS prevention
    for key, value in form_data.items():
        if isinstance(value, str) and any(char in value for char in ['<', '>', 'script', 'javascript:']):
            return False, "Invalid characters detected in form data."
    
    return True, ""


class DatabaseManager:
    """Database management utilities."""
    
    @staticmethod
    def safe_query(query_func, *args, **kwargs):
        """Safely execute database queries with error handling."""
        try:
            return query_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database query error: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def add_indexes():
        """Add database indexes for performance."""
        try:
            # Add indexes for common queries
            from sqlalchemy import Index
            
            # Index on email for faster lookups
            email_index = Index('idx_user_email', User.email)
            email_index.create(db.engine, checkfirst=True)
            
            # Index on role for role-based queries
            role_index = Index('idx_user_role', User.role)
            role_index.create(db.engine, checkfirst=True)
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")


def log_user_activity(user_id: int, action: str, details: str = ""):
    """Log user activity for audit purposes."""
    logger.info(f"User {user_id} performed action: {action} - {details}")


def is_safe_redirect(target: str) -> bool:
    """Check if redirect target is safe (prevents open redirect attacks)."""
    if not target:
        return False
    
    # Only allow relative URLs or same domain
    if target.startswith('/') and not target.startswith('//'):
        return True
    
    return False

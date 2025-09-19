"""
Error handling and logging utilities for LD Detector application.
Provides centralized error handling, logging, and user-friendly error messages.
"""
import logging
import traceback
from functools import wraps
from typing import Dict, Any, Optional
from flask import render_template, request, jsonify, current_app, flash, redirect, url_for
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from flask_wtf.csrf import CSRFError
import os


# Configure logging
def setup_logging():
    """Setup application logging configuration."""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'app.log')),
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


class ErrorHandler:
    """Centralized error handling class."""
    
    @staticmethod
    def log_error(error: Exception, context: str = "", user_id: Optional[int] = None):
        """Log error with context and user information."""
        logger = logging.getLogger(__name__)
        
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'user_id': user_id,
            'request_url': request.url if request else None,
            'request_method': request.method if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'traceback': traceback.format_exc()
        }
        
        logger.error(f"Error in {context}: {error_info}")
        
        # Log to separate error file for critical errors
        if isinstance(error, (SQLAlchemyError, Exception)):
            with open('logs/errors.log', 'a') as f:
                f.write(f"{error_info}\n\n")
    
    @staticmethod
    def handle_database_error(error: SQLAlchemyError, context: str = "") -> str:
        """Handle database-specific errors."""
        ErrorHandler.log_error(error, f"Database error in {context}")
        
        # Rollback any pending transactions
        try:
            from models import db
            db.session.rollback()
        except:
            pass
        
        # Return user-friendly message
        if "UNIQUE constraint failed" in str(error):
            return "This information already exists. Please check your input."
        elif "FOREIGN KEY constraint failed" in str(error):
            return "Invalid reference. Please refresh and try again."
        elif "NOT NULL constraint failed" in str(error):
            return "Required information is missing. Please fill all required fields."
        else:
            return "A database error occurred. Please try again later."
    
    @staticmethod
    def handle_validation_error(error: ValueError, context: str = "") -> str:
        """Handle validation errors."""
        ErrorHandler.log_error(error, f"Validation error in {context}")
        return str(error)  # Validation errors are usually user-friendly
    
    @staticmethod
    def handle_authentication_error(error: Exception, context: str = "") -> str:
        """Handle authentication-related errors."""
        ErrorHandler.log_error(error, f"Authentication error in {context}")
        return "Authentication failed. Please log in again."
    
    @staticmethod
    def handle_permission_error(error: Exception, context: str = "") -> str:
        """Handle permission-related errors."""
        ErrorHandler.log_error(error, f"Permission error in {context}")
        return "You don't have permission to perform this action."
    
    @staticmethod
    def get_user_friendly_message(error: Exception, context: str = "") -> str:
        """Get user-friendly error message based on error type."""
        if isinstance(error, SQLAlchemyError):
            return ErrorHandler.handle_database_error(error, context)
        elif isinstance(error, ValueError):
            return ErrorHandler.handle_validation_error(error, context)
        elif "authentication" in str(error).lower() or "login" in str(error).lower():
            return ErrorHandler.handle_authentication_error(error, context)
        elif "permission" in str(error).lower() or "access" in str(error).lower():
            return ErrorHandler.handle_permission_error(error, context)
        else:
            ErrorHandler.log_error(error, context)
            return "An unexpected error occurred. Please try again later."


def handle_errors(f):
    """Decorator for consistent error handling in routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except SQLAlchemyError as e:
            message = ErrorHandler.handle_database_error(e, f.__name__)
            flash(message, 'error')
            return redirect(url_for('index'))
        except ValueError as e:
            message = ErrorHandler.handle_validation_error(e, f.__name__)
            flash(message, 'error')
            return redirect(request.url)
        except HTTPException:
            # Re-raise HTTP exceptions (like 404, 403) to be handled by Flask
            raise
        except Exception as e:
            message = ErrorHandler.get_user_friendly_message(e, f.__name__)
            flash(message, 'error')
            return redirect(url_for('index'))
    
    return decorated_function


def handle_api_errors(f):
    """Decorator for API route error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except SQLAlchemyError as e:
            ErrorHandler.handle_database_error(e, f.__name__)
            return jsonify({'error': 'Database error occurred'}), 500
        except ValueError as e:
            ErrorHandler.handle_validation_error(e, f.__name__)
            return jsonify({'error': str(e)}), 400
        except HTTPException:
            raise
        except Exception as e:
            ErrorHandler.get_user_friendly_message(e, f.__name__)
            return jsonify({'error': 'Internal server error'}), 500
    
    return decorated_function


def register_error_handlers(app):
    """Register global error handlers with Flask app."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        ErrorHandler.log_error(error, "404 Not Found")
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors."""
        ErrorHandler.log_error(error, "403 Forbidden")
        flash('Access denied. You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        ErrorHandler.log_error(error, "500 Internal Server Error")
        from models import db
        db.session.rollback()
        flash('An unexpected error occurred. Please try again later.', 'error')
        return redirect(url_for('index'))
    
    @app.errorhandler(CSRFError)
    def csrf_error(error):
        """Handle CSRF errors."""
        ErrorHandler.log_error(error, "CSRF Error")
        flash('Security token expired. Please try again.', 'error')
        return redirect(request.url or url_for('index'))


class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    @staticmethod
    def log_slow_query(query_time: float, query: str, context: str = ""):
        """Log slow database queries."""
        if query_time > 1.0:  # Log queries taking more than 1 second
            logger = logging.getLogger(__name__)
            logger.warning(f"Slow query detected in {context}: {query_time:.2f}s - {query}")
    
    @staticmethod
    def monitor_request_time(f):
        """Decorator to monitor request processing time."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                processing_time = end_time - start_time
                
                if processing_time > 2.0:  # Log requests taking more than 2 seconds
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Slow request detected: {f.__name__} took {processing_time:.2f}s")
        
        return decorated_function


class SecurityLogger:
    """Log security-related events."""
    
    @staticmethod
    def log_login_attempt(email: str, success: bool, ip_address: str = None):
        """Log login attempts."""
        logger = logging.getLogger('security')
        status = "SUCCESS" if success else "FAILED"
        ip = ip_address or (request.remote_addr if request else "Unknown")
        
        logger.info(f"Login attempt: {email} - {status} - IP: {ip}")
        
        # Log failed attempts to security file
        if not success:
            with open('logs/security.log', 'a') as f:
                f.write(f"FAILED LOGIN: {email} - IP: {ip} - {request.url if request else 'Unknown'}\n")
    
    @staticmethod
    def log_suspicious_activity(activity: str, user_id: Optional[int] = None, details: str = ""):
        """Log suspicious activities."""
        logger = logging.getLogger('security')
        ip = request.remote_addr if request else "Unknown"
        
        logger.warning(f"Suspicious activity: {activity} - User: {user_id} - IP: {ip} - {details}")
        
        # Always log to security file
        with open('logs/security.log', 'a') as f:
            f.write(f"SUSPICIOUS: {activity} - User: {user_id} - IP: {ip} - {details}\n")
    
    @staticmethod
    def log_password_change(user_id: int, success: bool):
        """Log password change attempts."""
        logger = logging.getLogger('security')
        status = "SUCCESS" if success else "FAILED"
        ip = request.remote_addr if request else "Unknown"
        
        logger.info(f"Password change: User {user_id} - {status} - IP: {ip}")


def validate_request_data(required_fields: list, data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate request data for required fields and basic security.
    
    Args:
        required_fields: List of required field names
        data: Dictionary of data to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"{field.replace('_', ' ').title()} is required."
    
    # Basic XSS prevention
    for key, value in data.items():
        if isinstance(value, str):
            # Check for potentially dangerous content
            dangerous_patterns = ['<script', 'javascript:', 'onload=', 'onerror=']
            if any(pattern in value.lower() for pattern in dangerous_patterns):
                SecurityLogger.log_suspicious_activity(
                    "XSS attempt detected", 
                    details=f"Field: {key}, Content: {value[:100]}"
                )
                return False, "Invalid characters detected in form data."
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    import re
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length
    filename = filename[:100]
    
    return filename


# Initialize logging when module is imported
setup_logging()

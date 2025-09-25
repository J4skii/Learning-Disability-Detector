from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models.enhanced_models import db, User
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, ""

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Validation
        errors = []
        
        if len(name) < 2:
            errors.append('Name must be at least 2 characters long')
        
        if not validate_email(email):
            errors.append('Please enter a valid email address')
        
        is_valid_password, password_error = validate_password(password)
        if not is_valid_password:
            errors.append(password_error)
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if errors:
            for error in errors:
                flash(error)
            return render_template('signup.html')
        
        try:
            user = User(name=name, email=email, role='student')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! Please log in.')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your account. Please try again.')
            return render_template('signup.html')
    
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Invalid email or password')
            return render_template('login.html')
        
        # Check if account is locked
        if user.is_account_locked():
            flash('Account temporarily locked due to multiple failed login attempts. Please try again later.')
            return render_template('login.html')
        
        if user.check_password(password):
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            user.account_locked_until = None
            db.session.commit()
            
            session.permanent = True
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            flash('Logged in successfully!')
            return redirect(url_for('main.landing'))
        else:
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
                flash('Account locked due to multiple failed login attempts. Please try again in 30 minutes.')
            else:
                remaining = 5 - user.failed_login_attempts
                flash(f'Invalid email or password. {remaining} attempts remaining.')
            
            db.session.commit()
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not validate_email(email):
            flash('Please enter a valid email address')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                from app import mail, serializer
                token = serializer.dumps(email, salt='password-reset-salt')
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                
                msg = Message('Password Reset Request', recipients=[email])
                msg.body = f'''
Hello {user.name},

You have requested a password reset for your LD Detector account.

Please click the following link to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this reset, please ignore this email.

Best regards,
LD Detector Team
'''
                mail.send(msg)
                flash('Password reset email sent. Please check your inbox.')
            except Exception as e:
                flash('Error sending email. Please try again later.')
        else:
            # Don't reveal if email exists or not
            flash('If an account with that email exists, a reset link has been sent.')
        
        return redirect(url_for('auth.forgot_password'))
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        from app import serializer
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        flash('The password reset link is invalid or has expired.')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid user.')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        is_valid, error_message = validate_password(password)
        if not is_valid:
            flash(error_message)
            return render_template('reset_password.html')
        
        try:
            user.set_password(password)
            user.failed_login_attempts = 0  # Reset failed attempts
            user.account_locked_until = None
            db.session.commit()
            flash('Your password has been updated successfully. Please log in.')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating password. Please try again.')
    
    return render_template('reset_password.html')
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import csv
import re
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='student')
    completed_get_to_know_you = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    
    # User profile data
    age_group = db.Column(db.String(20))
    learning_style = db.Column(db.String(50))
    diagnosed_difficulties = db.Column(db.String(100))
    
    # Relationships
    results = db.relationship('Result', backref='user', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint('length(name) >= 2', name='name_min_length'),
        CheckConstraint("email LIKE '%@%'", name='email_format'),
    )

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_account_locked(self):
        if self.account_locked_until:
            return datetime.utcnow() < self.account_locked_until
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Result(db.Model):
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    test_type = db.Column(db.String(50), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, default=5)
    confidence_score = db.Column(db.Float)  # ML confidence
    flag = db.Column(db.Boolean, nullable=False)
    message = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Assessment metadata
    time_taken = db.Column(db.Integer)  # seconds
    responses = db.Column(db.JSON)  # Store raw responses
    response_times = db.Column(db.JSON)  # Time per question
    
    __table_args__ = (
        CheckConstraint('score >= 0', name='score_non_negative'),
        CheckConstraint('score <= max_score', name='score_within_range'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='confidence_range'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'test_type': self.test_type,
            'score': self.score,
            'max_score': self.max_score,
            'confidence_score': self.confidence_score,
            'flag': self.flag,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class AssessmentSession(db.Model):
    __tablename__ = 'assessment_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    session_data = db.Column(db.JSON)  # Store progress

def save_result(user_id, test_type, score, flag, message, **kwargs):
    """Enhanced result saving with additional metadata"""
    result = Result(
        user_id=user_id,
        test_type=test_type,
        score=score,
        flag=bool(flag),
        message=message,
        confidence_score=kwargs.get('confidence_score'),
        recommendations=kwargs.get('recommendations'),
        time_taken=kwargs.get('time_taken'),
        responses=kwargs.get('responses'),
        response_times=kwargs.get('response_times')
    )
    db.session.add(result)
    db.session.commit()
    return result

def get_filtered_results(email=None, test_type=None, user_id=None):
    """Enhanced filtering with user relationship"""
    query = db.session.query(Result).join(User)
    
    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))
    if test_type:
        query = query.filter(Result.test_type == test_type)
    if user_id:
        query = query.filter(Result.user_id == user_id)
    
    return query.order_by(Result.timestamp.desc()).all()

def export_results_to_csv(email=None, test_type=None):
    """Enhanced CSV export with user data"""
    results = get_filtered_results(email=email, test_type=test_type)
    filename = f"exported_results_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'User ID', 'Name', 'Email', 'Test Type', 'Score', 'Max Score',
            'Confidence', 'Flag', 'Message', 'Time Taken', 'Timestamp'
        ])
        
        for r in results:
            writer.writerow([
                r.user_id, r.user.name, r.user.email, r.test_type,
                r.score, r.max_score, r.confidence_score or 'N/A',
                'Yes' if r.flag else 'No', r.message,
                r.time_taken or 'N/A', r.timestamp
            ])
    
    return filename
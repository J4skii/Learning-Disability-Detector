from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, ForeignKeyConstraint
from sqlalchemy.orm import validates

from datetime import datetime
import csv
import re
import logging
import os

db = SQLAlchemy()
logger = logging.getLogger(__name__)

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='student', index=True)
    completed_get_to_know_you = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # New fields for student info
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(20), nullable=True)

    # Get to Know You responses
    g2k_learning_style = db.Column(db.String(50), nullable=True)
    g2k_diagnosed_difficulties = db.Column(db.String(100), nullable=True)
    g2k_age_group = db.Column(db.String(20), nullable=True)

    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        if not email:
            raise ValueError('Email is required')
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError('Invalid email format')
        
        return email.lower().strip()

    @validates('name')
    def validate_name(self, key, name):
        """Validate name format."""
        if not name or len(name.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        
        # Allow letters, spaces, hyphens, and apostrophes
        name_pattern = r"^[a-zA-Z\s\-']+$"
        if not re.match(name_pattern, name.strip()):
            raise ValueError('Name contains invalid characters')
        
        return name.strip()

    @validates('age')
    def validate_age(self, key, age):
        """Validate age."""
        if age is not None and (age < 1 or age > 120):
            raise ValueError('Age must be between 1 and 120')
        return age

    @validates('role')
    def validate_role(self, key, role):
        """Validate user role."""
        valid_roles = ['student', 'counselor', 'admin', 'superuser']
        if role not in valid_roles:
            raise ValueError(f'Invalid role. Must be one of: {valid_roles}')
        return role

    def set_password(self, password):
        """Set password with basic validation."""
        if len(password) < 6:
            raise ValueError('Password must be at least 6 characters long')
        
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password with error handling."""
        try:
            return check_password_hash(self.password_hash, password)
        except Exception as e:
            logger.error(f"Password check error for user {self.id}: {e}")
            return False

    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'age': self.age,
            'gender': self.gender,
            'course': self.course,
            'year': self.year,
            'completed_get_to_know_you': self.completed_get_to_know_you,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f'<User {self.email}>'
    
class Result(db.Model):
    __tablename__ = 'result'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, index=True)
    test_type = db.Column(db.String(50), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    flag = db.Column(db.Boolean, default=False)
    message = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('results', lazy=True))
    
    @validates('score')
    def validate_score(self, key, score):
        """Validate test score."""
        if not isinstance(score, int) or score < 0 or score > 100:
            raise ValueError('Score must be an integer between 0 and 100')
        return score
    
    @validates('test_type')
    def validate_test_type(self, key, test_type):
        """Validate test type."""
        valid_types = ['Dyslexia', 'Dyscalculia', 'Working Memory', 'Flash Cards']
        if test_type not in valid_types:
            raise ValueError(f'Invalid test type. Must be one of: {valid_types}')
        return test_type
    
    def to_dict(self):
        """Convert result to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'test_type': self.test_type,
            'score': self.score,
            'flag': self.flag,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        return f'<Result {self.test_type} - {self.score}>'

class Test(db.Model):
    __tablename__ = 'test'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    difficulty_level = db.Column(db.String(20), default='medium', index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    remedials = db.relationship('Remedial', backref='test', lazy=True, cascade='all, delete-orphan')
    
    @validates('difficulty_level')
    def validate_difficulty_level(self, key, difficulty_level):
        """Validate difficulty level."""
        valid_levels = ['easy', 'medium', 'hard']
        if difficulty_level not in valid_levels:
            raise ValueError(f'Invalid difficulty level. Must be one of: {valid_levels}')
        return difficulty_level
    
    def to_dict(self):
        """Convert test to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'difficulty_level': self.difficulty_level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Test {self.name}>'

class Remedial(db.Model):
    __tablename__ = 'remedial'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)  # Text or URL to resources
    function = db.Column(db.Text, nullable=True)  # Description of remedial purpose
    difficulty_level = db.Column(db.String(20), default='medium')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @validates('difficulty_level')
    def validate_difficulty_level(self, key, difficulty_level):
        """Validate difficulty level."""
        valid_levels = ['easy', 'medium', 'hard']
        if difficulty_level not in valid_levels:
            raise ValueError(f'Invalid difficulty level. Must be one of: {valid_levels}')
        return difficulty_level
    
    def to_dict(self):
        """Convert remedial to dictionary."""
        return {
            'id': self.id,
            'test_id': self.test_id,
            'name': self.name,
            'description': self.description,
            'content': self.content,
            'function': self.function,
            'difficulty_level': self.difficulty_level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Remedial {self.name}>'

class User_Test_Attempt(db.Model):
    __tablename__ = 'user_test_attempt'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False, index=True)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    score = db.Column(db.Integer, nullable=True)
    flag = db.Column(db.Boolean, default=False)  # Indicates learning difficulty
    message = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # In seconds
    
    # Relationships
    user = db.relationship('User', backref=db.backref('test_attempts', lazy=True))
    test = db.relationship('Test', backref=db.backref('attempts', lazy=True))
    
    @validates('score')
    def validate_score(self, key, score):
        """Validate test score."""
        if score is not None and (score < 0 or score > 100):
            raise ValueError('Score must be between 0 and 100')
        return score
    
    @validates('duration')
    def validate_duration(self, key, duration):
        """Validate duration."""
        if duration is not None and (duration < 0 or duration > 3600):  # Max 1 hour
            raise ValueError('Duration must be between 0 and 3600 seconds')
        return duration
    
    def to_dict(self):
        """Convert attempt to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'test_id': self.test_id,
            'attempt_date': self.attempt_date.isoformat() if self.attempt_date else None,
            'score': self.score,
            'flag': self.flag,
            'message': self.message,
            'duration': self.duration
        }
    
    def __repr__(self):
        return f'<User_Test_Attempt {self.user_id} - {self.test_id}>'

class User_Remedial_Progress(db.Model):
    __tablename__ = 'user_remedial_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    remedial_id = db.Column(db.Integer, db.ForeignKey('remedial.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='started')  # started, in_progress, completed
    progress_percentage = db.Column(db.Integer, default=0)  # 0-100
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)  # Counselor feedback
    
    # Relationships
    user = db.relationship('User', backref=db.backref('remedial_progress', lazy=True))
    remedial = db.relationship('Remedial', backref=db.backref('user_progress', lazy=True))
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate progress status."""
        valid_statuses = ['started', 'in_progress', 'completed', 'paused']
        if status not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return status
    
    @validates('progress_percentage')
    def validate_progress_percentage(self, key, progress_percentage):
        """Validate progress percentage."""
        if not isinstance(progress_percentage, int) or progress_percentage < 0 or progress_percentage > 100:
            raise ValueError('Progress percentage must be an integer between 0 and 100')
        return progress_percentage
    
    def to_dict(self):
        """Convert progress to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'remedial_id': self.remedial_id,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes
        }
    
    def __repr__(self):
        return f'<User_Remedial_Progress {self.user_id} - {self.remedial_id}>'

class Test_Attempt(db.Model):
    """Track individual test attempts with difficulty progression."""
    __tablename__ = 'test_attempt'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    test_type = db.Column(db.String(50), nullable=False, index=True)  # dyslexia, dyscalculia, memory, flash_cards
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    difficulty_level = db.Column(db.String(20), nullable=False, default='easy')  # easy, medium, hard
    score = db.Column(db.Integer, nullable=False)
    questions_used = db.Column(db.Text)  # JSON string of question IDs used
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('user_test_attempts', lazy=True))
    
    @validates('test_type')
    def validate_test_type(self, key, test_type):
        """Validate test type."""
        valid_types = ['dyslexia', 'dyscalculia', 'memory', 'flash_cards']
        if test_type not in valid_types:
            raise ValueError(f'Invalid test type. Must be one of: {valid_types}')
        return test_type
    
    @validates('difficulty_level')
    def validate_difficulty_level(self, key, difficulty_level):
        """Validate difficulty level."""
        valid_levels = ['easy', 'medium', 'hard']
        if difficulty_level not in valid_levels:
            raise ValueError(f'Invalid difficulty level. Must be one of: {valid_levels}')
        return difficulty_level
    
    @validates('score')
    def validate_score(self, key, score):
        """Validate score."""
        if not isinstance(score, int) or score < 0 or score > 100:
            raise ValueError('Score must be an integer between 0 and 100')
        return score
    
    def to_dict(self):
        """Convert attempt to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'test_type': self.test_type,
            'attempt_number': self.attempt_number,
            'difficulty_level': self.difficulty_level,
            'score': self.score,
            'questions_used': self.questions_used,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self):
        return f'<Test_Attempt {self.user_id} - {self.test_type} - Attempt {self.attempt_number}>'

class Question_Bank(db.Model):
    """Question banks for different test types and difficulty levels."""
    __tablename__ = 'question_bank'
    
    id = db.Column(db.Integer, primary_key=True)
    test_type = db.Column(db.String(50), nullable=False, index=True)  # dyslexia, dyscalculia, memory, flash_cards
    difficulty_level = db.Column(db.String(20), nullable=False, index=True)  # easy, medium, hard
    category = db.Column(db.String(100), nullable=False, index=True)  # e.g., "phonetics", "arithmetic", "visual_memory"
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(500), nullable=False)
    options = db.Column(db.Text)  # JSON string for multiple choice options
    question_data = db.Column(db.Text)  # Additional data (images, etc.) as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @validates('test_type')
    def validate_test_type(self, key, test_type):
        """Validate test type."""
        valid_types = ['dyslexia', 'dyscalculia', 'memory', 'flash_cards']
        if test_type not in valid_types:
            raise ValueError(f'Invalid test type. Must be one of: {valid_types}')
        return test_type
    
    @validates('difficulty_level')
    def validate_difficulty_level(self, key, difficulty_level):
        """Validate difficulty level."""
        valid_levels = ['easy', 'medium', 'hard']
        if difficulty_level not in valid_levels:
            raise ValueError(f'Invalid difficulty level. Must be one of: {valid_levels}')
        return difficulty_level
    
    def to_dict(self):
        """Convert question to dictionary."""
        return {
            'id': self.id,
            'test_type': self.test_type,
            'difficulty_level': self.difficulty_level,
            'category': self.category,
            'question_text': self.question_text,
            'correct_answer': self.correct_answer,
            'options': self.options,
            'question_data': self.question_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Question_Bank {self.test_type} - {self.difficulty_level} - {self.category}>'

def save_result(name, email, test_type, score, flag, message, user_id=None):
    """Save test result with validation and error handling."""
    try:
        # Validate inputs
        if not name or not email or not test_type:
            raise ValueError("Name, email, and test_type are required")
        
        if not isinstance(score, int) or score < 0 or score > 100:
            raise ValueError("Score must be an integer between 0 and 100")
        
        # Sanitize inputs
        name = name.strip()[:150]
        email = email.strip().lower()[:150]
        message = message.strip()[:255] if message else None
        
        # Create result
        result = Result(
            user_id=user_id,
            name=name,
            email=email,
            test_type=test_type,
            score=score,
            flag=bool(flag),
            message=message
        )
        
        db.session.add(result)
        db.session.commit()
        
        logger.info(f"Result saved for user {email}: {test_type} - {score}")
        return result
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving result: {e}")
        raise

def get_filtered_results(email=None, test_type=None, limit=None):
    """Get filtered results with security validation."""
    try:
        query = Result.query.order_by(Result.timestamp.desc())
        
        if email:
            # Sanitize email input
            email = email.strip().lower()
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise ValueError("Invalid email format")
            query = query.filter(Result.email.ilike(f"%{email}%"))
        
        if test_type:
            # Validate test type
            valid_types = ['Dyslexia', 'Dyscalculia', 'Working Memory', 'Flash Cards']
            if test_type not in valid_types:
                raise ValueError(f"Invalid test type. Must be one of: {valid_types}")
            query = query.filter(Result.test_type == test_type)
        
        if limit and isinstance(limit, int) and limit > 0:
            query = query.limit(min(limit, 1000))  # Max 1000 results
        
        return query.all()
        
    except Exception as e:
        logger.error(f"Error getting filtered results: {e}")
        return []

def export_results_to_csv(email=None, test_type=None):
    """Export results to CSV with security validation."""
    try:
        results = get_filtered_results(email=email, test_type=test_type)
        
        # Create secure filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"exported_results_{timestamp}.csv"
        
        # Sanitize filename to prevent path traversal
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Write to file with proper encoding
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Email', 'Test Type', 'Score', 'Flag', 'Message', 'Timestamp'])
            
            for result in results:
                # Sanitize data before writing
                name = result.name.replace('\n', ' ').replace('\r', ' ')
                email = result.email.replace('\n', ' ').replace('\r', ' ')
                message = result.message.replace('\n', ' ').replace('\r', ' ') if result.message else ''
                
                writer.writerow([
                    name, email, result.test_type, result.score,
                    'Yes' if result.flag else 'No', message,
                    result.timestamp.strftime('%Y-%m-%d %H:%M:%S') if result.timestamp else ''
                ])
        
        logger.info(f"Results exported to {filename}: {len(results)} records")
        return filename
        
    except Exception as e:
        logger.error(f"Error exporting results to CSV: {e}")
        raise

def save_attempt(user_id, test_id, score, flag, message, duration=None):
    """Save test attempt with validation."""
    try:
        # Validate inputs
        if not user_id or not test_id:
            raise ValueError("User ID and Test ID are required")
        
        if score is not None and (score < 0 or score > 100):
            raise ValueError("Score must be between 0 and 100")
        
        if duration is not None and (duration < 0 or duration > 3600):
            raise ValueError("Duration must be between 0 and 3600 seconds")
        
        # Sanitize message
        message = message.strip()[:255] if message else None
        
        attempt = User_Test_Attempt(
            user_id=user_id,
            test_id=test_id,
            score=score,
            flag=bool(flag),
            message=message,
            duration=duration
        )
        
        db.session.add(attempt)
        db.session.commit()
        
        logger.info(f"Test attempt saved for user {user_id}, test {test_id}")
        return attempt
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving attempt: {e}")
        raise

def get_user_attempts(user_id=None, test_id=None, limit=None):
    """Get user attempts with validation."""
    try:
        query = User_Test_Attempt.query.order_by(User_Test_Attempt.attempt_date.desc())
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        if test_id:
            query = query.filter_by(test_id=test_id)
        
        if limit and isinstance(limit, int) and limit > 0:
            query = query.limit(min(limit, 100))  # Max 100 attempts
        
        return query.all()
        
    except Exception as e:
        logger.error(f"Error getting user attempts: {e}")
        return []

def save_remedial_progress(user_id, remedial_id, status, progress_percentage, notes=None):
    """Save remedial progress with validation."""
    try:
        # Validate inputs
        if not user_id or not remedial_id:
            raise ValueError("User ID and Remedial ID are required")
        
        valid_statuses = ['started', 'in_progress', 'completed', 'paused']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        if not isinstance(progress_percentage, int) or progress_percentage < 0 or progress_percentage > 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        
        # Sanitize notes
        notes = notes.strip()[:1000] if notes else None
        
        # Get or create progress record
        progress = User_Remedial_Progress.query.filter_by(
            user_id=user_id, remedial_id=remedial_id
        ).first()
        
        if not progress:
            progress = User_Remedial_Progress(user_id=user_id, remedial_id=remedial_id)
            db.session.add(progress)
        
        # Update progress
        progress.status = status
        progress.progress_percentage = progress_percentage
        if notes:
            progress.notes = notes
        
        if status == 'completed':
            progress.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Remedial progress updated for user {user_id}, remedial {remedial_id}")
        return progress
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving remedial progress: {e}")
        raise

def get_user_remedial_progress(user_id=None, remedial_id=None, limit=None):
    """Get user remedial progress with validation."""
    try:
        query = User_Remedial_Progress.query.order_by(User_Remedial_Progress.started_at.desc())
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        if remedial_id:
            query = query.filter_by(remedial_id=remedial_id)
        
        if limit and isinstance(limit, int) and limit > 0:
            query = query.limit(min(limit, 100))  # Max 100 records
        
        return query.all()
        
    except Exception as e:
        logger.error(f"Error getting remedial progress: {e}")
        return []

def create_sample_tests_and_remedials():
    """Create sample tests and remedials if they don't exist."""
    # Tests
    tests_data = [
        {'name': 'Comprehension', 'description': 'Reading comprehension test', 'difficulty_level': 'medium'},
        {'name': 'Memory Test', 'description': 'Short-term memory recall test', 'difficulty_level': 'medium'},
        {'name': 'Phonetics', 'description': 'Sound-letter mapping test', 'difficulty_level': 'easy'},
        {'name': 'Flash Card Test', 'description': 'Quick recognition and spelling test', 'difficulty_level': 'hard'}
    ]
    for data in tests_data:
        if not Test.query.filter_by(name=data['name']).first():
            test = Test(**data)
            db.session.add(test)
    db.session.commit()

    # Remedials (assuming tests are created)
    comprehension = Test.query.filter_by(name='Comprehension').first()
    memory = Test.query.filter_by(name='Memory Test').first()
    phonetics = Test.query.filter_by(name='Phonetics').first()
    flashcards = Test.query.filter_by(name='Flash Card Test').first()

    remedials_data = [
        {'test_id': comprehension.id if comprehension else 1, 'name': 'Guided Reading Exercise', 'description': 'Interactive passages with questions', 'function': 'Build reading comprehension through guided exercises'},
        {'test_id': memory.id if memory else 2, 'name': 'Memory Recall Game', 'description': 'Word sequence recall drills', 'function': 'Strengthen short-term memory with games'},
        {'test_id': phonetics.id if phonetics else 3, 'name': 'Sound Mapping Drill', 'description': 'Pronunciation and letter-sound practice', 'function': 'Enhance phonetic awareness'},
        {'test_id': flashcards.id if flashcards else 4, 'name': 'Spelling Flash Cards', 'description': 'Timed word recognition', 'function': 'Improve spelling and quick recognition'}
    ]
    for data in remedials_data:
        if not Remedial.query.filter_by(name=data['name']).first():
            remedial = Remedial(**data)
            db.session.add(remedial)
    db.session.commit()

def create_question_banks():
    """Create sample question banks for all test types and difficulty levels."""
    try:
        import json
        
        # Sample dyslexia questions
        dyslexia_questions = [
            # Easy level
            {'test_type': 'dyslexia', 'difficulty_level': 'easy', 'category': 'phonetics',
             'question_text': 'Which word sounds different?', 'correct_answer': 'b',
             'options': json.dumps(['a) cat', 'b) kite', 'c) bat', 'd) hat'])},
            {'test_type': 'dyslexia', 'difficulty_level': 'easy', 'category': 'phonetics',
             'question_text': 'Which word rhymes with "dog"?', 'correct_answer': 'a',
             'options': json.dumps(['a) fog', 'b) cat', 'c) bird', 'd) fish'])},
            
            # Medium level
            {'test_type': 'dyslexia', 'difficulty_level': 'medium', 'category': 'reading_comprehension',
             'question_text': 'Read: "The quick brown fox jumps over the lazy dog." What did the fox jump over?', 'correct_answer': 'b',
             'options': json.dumps(['a) A fence', 'b) The lazy dog', 'c) A river', 'd) A tree'])},
            {'test_type': 'dyslexia', 'difficulty_level': 'medium', 'category': 'word_recognition',
             'question_text': 'Which word is spelled correctly?', 'correct_answer': 'a',
             'options': json.dumps(['a) beautiful', 'b) beutiful', 'c) beatiful', 'd) beutifull'])},
            
            # Hard level
            {'test_type': 'dyslexia', 'difficulty_level': 'hard', 'category': 'complex_reading',
             'question_text': 'Read: "The phenomenon of dyslexia affects approximately 15-20% of the population." What percentage is affected?', 'correct_answer': 'c',
             'options': json.dumps(['a) 10-15%', 'b) 20-25%', 'c) 15-20%', 'd) 25-30%'])},
        ]
        
        # Sample dyscalculia questions
        dyscalculia_questions = [
            # Easy level
            {'test_type': 'dyscalculia', 'difficulty_level': 'easy', 'category': 'basic_arithmetic',
             'question_text': 'What is 2 + 3?', 'correct_answer': 'a',
             'options': json.dumps(['a) 5', 'b) 6', 'c) 4', 'd) 7'])},
            {'test_type': 'dyscalculia', 'difficulty_level': 'easy', 'category': 'number_recognition',
             'question_text': 'Which number comes after 7?', 'correct_answer': 'b',
             'options': json.dumps(['a) 6', 'b) 8', 'c) 9', 'd) 10'])},
            
            # Medium level
            {'test_type': 'dyscalculia', 'difficulty_level': 'medium', 'category': 'multiplication',
             'question_text': 'What is 4 × 3?', 'correct_answer': 'c',
             'options': json.dumps(['a) 10', 'b) 11', 'c) 12', 'd) 13'])},
            {'test_type': 'dyscalculia', 'difficulty_level': 'medium', 'category': 'fractions',
             'question_text': 'What is 1/2 of 8?', 'correct_answer': 'b',
             'options': json.dumps(['a) 3', 'b) 4', 'c) 5', 'd) 6'])},
            
            # Hard level
            {'test_type': 'dyscalculia', 'difficulty_level': 'hard', 'category': 'word_problems',
             'question_text': 'If you have 24 apples and you want to share them equally among 6 friends, how many apples does each friend get?', 'correct_answer': 'a',
             'options': json.dumps(['a) 4', 'b) 3', 'c) 5', 'd) 6'])},
        ]
        
        # Sample memory questions
        memory_questions = [
            # Easy level
            {'test_type': 'memory', 'difficulty_level': 'easy', 'category': 'visual_memory',
             'question_text': 'Remember these words: apple, banana, orange. What was the second word?', 'correct_answer': 'banana',
             'options': json.dumps([])},
            {'test_type': 'memory', 'difficulty_level': 'easy', 'category': 'number_sequence',
             'question_text': 'Remember this sequence: 1, 3, 5. What comes next?', 'correct_answer': '7',
             'options': json.dumps([])},
            
            # Medium level
            {'test_type': 'memory', 'difficulty_level': 'medium', 'category': 'word_list',
             'question_text': 'Remember these words: cat, dog, bird, fish, rabbit. How many animals were there?', 'correct_answer': '5',
             'options': json.dumps([])},
            {'test_type': 'memory', 'difficulty_level': 'medium', 'category': 'pattern_recognition',
             'question_text': 'Remember this pattern: red, blue, red, blue, red. What color comes next?', 'correct_answer': 'blue',
             'options': json.dumps([])},
            
            # Hard level
            {'test_type': 'memory', 'difficulty_level': 'hard', 'category': 'complex_sequence',
             'question_text': 'Remember this sequence: 2, 4, 8, 16. What comes next?', 'correct_answer': '32',
             'options': json.dumps([])},
        ]
        
        # Sample flash card questions
        flashcard_questions = [
            # Easy level
            {'test_type': 'flash_cards', 'difficulty_level': 'easy', 'category': 'basic_words',
             'question_text': 'What do you see? [CAT image]', 'correct_answer': 'cat',
             'options': json.dumps([])},
            {'test_type': 'flash_cards', 'difficulty_level': 'easy', 'category': 'basic_words',
             'question_text': 'What do you see? [DOG image]', 'correct_answer': 'dog',
             'options': json.dumps([])},
            
            # Medium level
            {'test_type': 'flash_cards', 'difficulty_level': 'medium', 'category': 'animals',
             'question_text': 'What animal is this? [ELEPHANT image]', 'correct_answer': 'elephant',
             'options': json.dumps([])},
            {'test_type': 'flash_cards', 'difficulty_level': 'medium', 'category': 'objects',
             'question_text': 'What is this object? [BICYCLE image]', 'correct_answer': 'bicycle',
             'options': json.dumps([])},
            
            # Hard level
            {'test_type': 'flash_cards', 'difficulty_level': 'hard', 'category': 'complex_objects',
             'question_text': 'What is this? [MICROSCOPE image]', 'correct_answer': 'microscope',
             'options': json.dumps([])},
        ]
        
        all_questions = dyslexia_questions + dyscalculia_questions + memory_questions + flashcard_questions
        
        # Add questions to database
        for q_data in all_questions:
            existing = Question_Bank.query.filter_by(
                test_type=q_data['test_type'],
                difficulty_level=q_data['difficulty_level'],
                question_text=q_data['question_text']
            ).first()
            
            if not existing:
                question = Question_Bank(**q_data)
                db.session.add(question)
        
        db.session.commit()
        logger.info("Question banks created successfully")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating question banks: {e}")
        return False

def get_next_difficulty_level(user_id, test_type):
    """Determine the next difficulty level based on user's previous attempts."""
    try:
        # Get user's last 2 attempts for this test type
        last_attempts = Test_Attempt.query.filter_by(
            user_id=user_id, 
            test_type=test_type
        ).order_by(Test_Attempt.attempt_number.desc()).limit(2).all()
        
        if len(last_attempts) < 2:
            # First or second attempt - start with easy
            return 'easy'
        
        # Check scores from last 2 attempts
        recent_scores = [attempt.score for attempt in last_attempts[:2]]
        avg_score = sum(recent_scores) / len(recent_scores)
        
        # If average score is 70 or higher, increase difficulty
        if avg_score >= 70:
            current_level = last_attempts[0].difficulty_level
            if current_level == 'easy':
                return 'medium'
            elif current_level == 'medium':
                return 'hard'
            else:
                return 'hard'  # Stay at hard level
        else:
            # Keep current difficulty or decrease if struggling
            current_level = last_attempts[0].difficulty_level
            if current_level == 'hard' and avg_score < 50:
                return 'medium'
            elif current_level == 'medium' and avg_score < 40:
                return 'easy'
            else:
                return current_level
                
    except Exception as e:
        logger.error(f"Error determining difficulty level: {e}")
        return 'easy'  # Default to easy on error

def get_questions_for_test(test_type, difficulty_level, count=5):
    """Get random questions for a specific test type and difficulty level."""
    try:
        questions = Question_Bank.query.filter_by(
            test_type=test_type,
            difficulty_level=difficulty_level
        ).order_by(db.func.random()).limit(count).all()
        
        return questions
    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        return []

def save_test_attempt(user_id, test_type, difficulty_level, score, questions_used):
    """Save a test attempt with difficulty progression tracking."""
    try:
        import json
        
        # Get next attempt number
        last_attempt = Test_Attempt.query.filter_by(
            user_id=user_id,
            test_type=test_type
        ).order_by(Test_Attempt.attempt_number.desc()).first()
        
        attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1
        
        # Create new attempt
        attempt = Test_Attempt(
            user_id=user_id,
            test_type=test_type,
            attempt_number=attempt_number,
            difficulty_level=difficulty_level,
            score=score,
            questions_used=json.dumps(questions_used) if questions_used else None
        )
        
        db.session.add(attempt)
        db.session.commit()
        
        logger.info(f"Test attempt saved: User {user_id}, {test_type}, attempt {attempt_number}, score {score}")
        return attempt
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving test attempt: {e}")
        return None

def create_hardcoded_users():
    """Create default admin and counselor users if they don't exist."""
    try:
        # Use simple passwords for development/testing
        admin_password = 'admin123'
        counselor_password = 'counselor123'
        
        # Admin user
        admin = User.query.filter_by(email='admin@lddetector.com').first()
        if not admin:
            admin = User(
                name='Administrator',
                email='admin@lddetector.com',
                role='admin',
                age=30,
                gender='Other',
                course='N/A',
                year='N/A'
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            logger.info("Default admin user created")

        # Counselor user
        counselor = User.query.filter_by(email='counselor@lddetector.com').first()
        if not counselor:
            counselor = User(
                name='Counselor',
                email='counselor@lddetector.com',
                role='counselor',
                age=28,
                gender='Other',
                course='N/A',
                year='N/A'
            )
            counselor.set_password(counselor_password)
            db.session.add(counselor)
            logger.info("Default counselor user created")

        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating default users: {e}")
        raise

if __name__ == "__main__":
    app.run(debug=True)

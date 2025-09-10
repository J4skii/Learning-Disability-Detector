from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
import csv

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='student')
    completed_get_to_know_you = db.Column(db.Boolean, default=False)

    # New fields for student info
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(20), nullable=True)

    # Get to Know You responses
    g2k_learning_style = db.Column(db.String(50), nullable=True)
    g2k_diagnosed_difficulties = db.Column(db.String(100), nullable=True)
    g2k_age_group = db.Column(db.String(20), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    test_type = db.Column(db.String(50))
    score = db.Column(db.Integer)
    flag = db.Column(db.Boolean)
    message = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def save_result(name, email, test_type, score, flag, message):
    r = Result(name=name, email=email, test_type=test_type, score=score, flag=bool(flag), message=message)
    db.session.add(r)
    db.session.commit()

def get_filtered_results(email=None, test_type=None):
    q = Result.query.order_by(Result.timestamp.desc())
    if email:
        q = q.filter(Result.email.ilike(f"%{email}%"))
    if test_type:
        q = q.filter(Result.test_type == test_type)
    return q.all()

def export_results_to_csv(email=None, test_type=None):
    results = get_filtered_results(email=email, test_type=test_type)
    filename = f"exported_results_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    # write to file in project folder
    path = filename
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Email', 'Test Type', 'Score', 'Flag', 'Message', 'Timestamp'])
        for r in results:
            writer.writerow([r.name, r.email, r.test_type, r.score, 'Yes' if r.flag else 'No', r.message, r.timestamp])
    return path

def create_hardcoded_users():
    """Create hardcoded admin and counselor users if they don't exist."""
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
        admin.set_password('admin123')  # Hardcoded password
        db.session.add(admin)

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
        counselor.set_password('counselor123')  # Hardcoded password
        db.session.add(counselor)

    db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)

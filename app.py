from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash
from models import db, User, save_result, get_filtered_results, export_results_to_csv
from ld_logic import evaluate_dyslexia, evaluate_dyscalculia, evaluate_memory
import os
from io import BytesIO
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'devkey')  # Needed for session

# Use DATABASE_URL env var if set (for Render). Fallback to sqlite for local testing.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration (example using Gmail SMTP, adjust as needed)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

mail = Mail(app)
db.init_app(app)

serializer = URLSafeTimedSerializer(app.secret_key)

def initialize_database():
    """Initialize database with error handling for corruption."""
    try:
        with app.app_context():
            db.create_all()
            print("Database initialized successfully!")
    except Exception as e:
        print(f"Database error: {e}")
        # If using SQLite and database is corrupted, remove it and recreate
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI'] and 'malformed' in str(e):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path):
                print(f"Removing corrupted database file: {db_path}")
                os.remove(db_path)
                print("Creating fresh database...")
                with app.app_context():
                    db.create_all()
                    print("Fresh database created successfully!")
            else:
                raise e
        else:
            raise e

# Initialize database with error handling
initialize_database()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('signup'))
        user = User(name=name, email=email, role='student')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Logged in successfully!')
            return redirect(url_for('index'))
        flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html', db=db, User=User)

@app.route('/landing')
def landing():
    return redirect(url_for('index'))

@app.route('/get-to-know-you', methods=['GET', 'POST'])
def get_to_know_you():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if user.completed_get_to_know_you:
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Process answers here (for now just mark as completed)
        user.completed_get_to_know_you = True
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('get_to_know_you.html', user=user)

@app.route('/test/dyslexia', methods=['GET', 'POST'])
def test_dyslexia():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if not user.completed_get_to_know_you:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        answers = [request.form.get(f'q{i}') for i in range(1,6)]
        result = evaluate_dyslexia(answers)
        save_result(name, email, result['type'], result['score'], result['flag'], result['message'])
        return render_template('results.html', result=result)
    return render_template('test_dyslexia.html')

@app.route('/test/dyscalculia', methods=['GET', 'POST'])
def test_dyscalculia():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if not user.completed_get_to_know_you:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        answers = [request.form.get(f'q{i}') for i in range(1,6)]
        result = evaluate_dyscalculia(answers)
        save_result(name, email, result['type'], result['score'], result['flag'], result['message'])
        return render_template('results.html', result=result)
    return render_template('test_dyscalculia.html')

@app.route('/test/memory', methods=['GET', 'POST'])
def test_memory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if not user.completed_get_to_know_you:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        answers = request.form.getlist('recall')
        result = evaluate_memory(answers)
        save_result(name, email, result['type'], result['score'], result['flag'], result['message'])
        return render_template('results.html', result=result)
    return render_template('test_memory.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', recipients=[email])
            msg.body = f'Please click the link to reset your password: {reset_url}'
            mail.send(msg)
            flash('Password reset email sent. Please check your inbox.')
        else:
            flash('Email not found.')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        flash('The password reset link is invalid or has expired.')
        return redirect(url_for('forgot_password'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid user.')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated. Please log in.')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    if user.role not in ['admin', 'superuser']:
        return redirect(url_for('index'))
    # Filters: email, test_type
    email = request.args.get('email', '').strip()
    test_type = request.args.get('test_type', '').strip()
    results = get_filtered_results(email=email or None, test_type=test_type or None)
    return render_template('admin_dashboard.html', results=results, email=email, test_type=test_type)

@app.route('/admin/export')
def admin_export():
    email = request.args.get('email', '').strip()
    test_type = request.args.get('test_type', '').strip()
    filename = export_results_to_csv(email=email or None, test_type=test_type or None)
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

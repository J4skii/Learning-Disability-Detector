from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.enhanced_models import db, User, save_result, AssessmentSession
from assessment.ml_engine import assessment_engine
from datetime import datetime
import json

assessments_bp = Blueprint('assessments', __name__)

def require_login(f):
    """Decorator to require user login"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access assessments.')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def require_profile_completion(f):
    """Decorator to require completed profile"""
    def decorated_function(*args, **kwargs):
        user = db.session.get(User, session['user_id'])
        if not user.completed_get_to_know_you:
            flash('Please complete the "Get to Know You" assessment first.')
            return redirect(url_for('main.landing'))
        return f(*args, **kwargs)
    return decorated_function

@assessments_bp.route('/test/dyslexia', methods=['GET', 'POST'])
@require_login
@require_profile_completion
def test_dyslexia():
    user = db.session.get(User, session['user_id'])
    
    if request.method == 'POST':
        # Collect form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        # Collect responses and timing data
        responses = []
        response_times = []
        
        for i in range(1, 6):  # 5 questions
            response = request.form.get(f'q{i}')
            if response:
                responses.append(response)
            
            # Get response time if available (from JavaScript)
            time_key = f'time_q{i}'
            if time_key in request.form:
                try:
                    response_times.append(float(request.form.get(time_key, 0)))
                except ValueError:
                    response_times.append(0)
        
        if len(responses) != 5:
            flash('Please answer all questions before submitting.')
            return render_template('test_dyslexia.html')
        
        # Get user profile for ML engine
        user_profile = {
            'age_group': user.age_group,
            'learning_style': user.learning_style,
            'diagnosed_difficulties': user.diagnosed_difficulties
        }
        
        # Evaluate using ML engine
        result = assessment_engine.evaluate_assessment(
            'dyslexia', responses, user_profile, response_times
        )
        
        # Save enhanced result
        save_result(
            user_id=user.id,
            test_type=result['type'],
            score=result['score'],
            flag=result['flag'],
            message=result['message'],
            confidence_score=result.get('confidence_score'),
            recommendations=result.get('recommendations'),
            time_taken=sum(response_times) if response_times else None,
            responses=responses,
            response_times=response_times
        )
        
        return render_template('results.html', result=result)
    
    return render_template('test_dyslexia.html')

@assessments_bp.route('/test/dyscalculia', methods=['GET', 'POST'])
@require_login
@require_profile_completion
def test_dyscalculia():
    user = db.session.get(User, session['user_id'])
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        responses = []
        response_times = []
        
        for i in range(1, 6):
            response = request.form.get(f'q{i}')
            if response:
                responses.append(response)
            
            time_key = f'time_q{i}'
            if time_key in request.form:
                try:
                    response_times.append(float(request.form.get(time_key, 0)))
                except ValueError:
                    response_times.append(0)
        
        if len(responses) != 5:
            flash('Please answer all questions before submitting.')
            return render_template('test_dyscalculia.html')
        
        user_profile = {
            'age_group': user.age_group,
            'learning_style': user.learning_style,
            'diagnosed_difficulties': user.diagnosed_difficulties
        }
        
        result = assessment_engine.evaluate_assessment(
            'dyscalculia', responses, user_profile, response_times
        )
        
        save_result(
            user_id=user.id,
            test_type=result['type'],
            score=result['score'],
            flag=result['flag'],
            message=result['message'],
            confidence_score=result.get('confidence_score'),
            recommendations=result.get('recommendations'),
            time_taken=sum(response_times) if response_times else None,
            responses=responses,
            response_times=response_times
        )
        
        return render_template('results.html', result=result)
    
    return render_template('test_dyscalculia.html')

@assessments_bp.route('/test/memory', methods=['GET', 'POST'])
@require_login
@require_profile_completion
def test_memory():
    user = db.session.get(User, session['user_id'])
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        # Get selected items
        selected_items = request.form.getlist('recall')
        
        # Get timing data if available
        study_time = request.form.get('study_time', 0)
        recall_time = request.form.get('recall_time', 0)
        
        try:
            study_time = float(study_time)
            recall_time = float(recall_time)
        except ValueError:
            study_time = recall_time = 0
        
        user_profile = {
            'age_group': user.age_group,
            'learning_style': user.learning_style,
            'diagnosed_difficulties': user.diagnosed_difficulties
        }
        
        result = assessment_engine.evaluate_assessment(
            'memory', selected_items, user_profile, [study_time, recall_time]
        )
        
        save_result(
            user_id=user.id,
            test_type=result['type'],
            score=result['score'],
            flag=result['flag'],
            message=result['message'],
            confidence_score=result.get('confidence_score'),
            recommendations=result.get('recommendations'),
            time_taken=int(study_time + recall_time),
            responses=selected_items,
            response_times=[study_time, recall_time]
        )
        
        return render_template('results.html', result=result)
    
    return render_template('test_memory.html')

@assessments_bp.route('/api/assessment/start', methods=['POST'])
@require_login
def start_assessment():
    """API endpoint to start an assessment session"""
    data = request.get_json()
    test_type = data.get('test_type')
    
    if test_type not in ['dyslexia', 'dyscalculia', 'memory']:
        return jsonify({'error': 'Invalid test type'}), 400
    
    # Create assessment session
    session_record = AssessmentSession(
        user_id=session['user_id'],
        test_type=test_type,
        session_data={'started_at': datetime.utcnow().isoformat()}
    )
    
    db.session.add(session_record)
    db.session.commit()
    
    return jsonify({
        'session_id': session_record.id,
        'test_type': test_type,
        'started_at': session_record.started_at.isoformat()
    })

@assessments_bp.route('/api/assessment/progress', methods=['POST'])
@require_login
def save_progress():
    """API endpoint to save assessment progress"""
    data = request.get_json()
    session_id = data.get('session_id')
    progress_data = data.get('progress')
    
    session_record = AssessmentSession.query.filter_by(
        id=session_id,
        user_id=session['user_id']
    ).first()
    
    if not session_record:
        return jsonify({'error': 'Session not found'}), 404
    
    # Update session data
    current_data = session_record.session_data or {}
    current_data.update(progress_data)
    session_record.session_data = current_data
    
    db.session.commit()
    
    return jsonify({'status': 'success'})
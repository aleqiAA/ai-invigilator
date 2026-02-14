from flask import Blueprint, request, jsonify
from database import db, Student, ExamSession, Alert
from functools import wraps
import secrets

api = Blueprint('api', __name__, url_prefix='/api/v1')

# API key authentication
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        # TODO: Store API keys in database
        if not api_key or api_key != 'your-api-key-here':
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated

# Create student
@api.route('/students', methods=['POST'])
@require_api_key
def create_student():
    data = request.json
    student = Student(
        name=data['name'],
        student_id=data['student_id'],
        email=data['email']
    )
    student.set_password(data.get('password', secrets.token_urlsafe(16)))
    student.email_verified = True
    db.session.add(student)
    db.session.commit()
    return jsonify({'id': student.id, 'student_id': student.student_id}), 201

# Get student
@api.route('/students/<student_id>', methods=['GET'])
@require_api_key
def get_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    return jsonify({
        'id': student.id,
        'name': student.name,
        'student_id': student.student_id,
        'email': student.email
    })

# Create exam session
@api.route('/exams', methods=['POST'])
@require_api_key
def create_exam():
    data = request.json
    student = Student.query.filter_by(student_id=data['student_id']).first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    session = ExamSession(
        student_id=student.id,
        exam_name=data['exam_name'],
        status='scheduled'
    )
    db.session.add(session)
    db.session.commit()
    
    # Return exam URL
    exam_url = f"/exam/{student.student_id}?session_id={session.id}"
    return jsonify({
        'session_id': session.id,
        'exam_url': exam_url,
        'embed_url': f"/embed/exam/{session.id}"
    }), 201

# Get exam results
@api.route('/exams/<int:session_id>', methods=['GET'])
@require_api_key
def get_exam_results(session_id):
    session = ExamSession.query.get(session_id)
    if not session:
        return jsonify({'error': 'Exam not found'}), 404
    
    alerts = Alert.query.filter_by(session_id=session_id).all()
    
    return jsonify({
        'session_id': session.id,
        'student_id': session.student.student_id,
        'exam_name': session.exam_name,
        'status': session.status,
        'start_time': session.start_time.isoformat() if session.start_time else None,
        'end_time': session.end_time.isoformat() if session.end_time else None,
        'integrity_score': max(0, 100 - (len(alerts) * 10)),
        'alerts': [{
            'type': a.alert_type,
            'severity': a.severity,
            'timestamp': a.timestamp.isoformat(),
            'description': a.description
        } for a in alerts]
    })

# Webhook for real-time alerts
@api.route('/webhooks/alerts', methods=['POST'])
@require_api_key
def webhook_alerts():
    # LMS can register webhook URL to receive real-time alerts
    return jsonify({'message': 'Webhook registered'}), 200

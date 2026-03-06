from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session as flask_session
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd
from io import BytesIO
from flask_wtf.csrf import CSRFProtect

LOCAL_TZ = pytz.timezone('Africa/Nairobi')

def get_local_time():
    return datetime.now(LOCAL_TZ)

from config import Config, get_config
from database import db, ExamSession, Invigilator, Student, Alert, Question, Answer, Admin, ActivityLog, Institution
try:
    from face_detection import FaceDetector
except ImportError:
    class FaceDetector: pass

try:
    from eye_tracking import EyeTracker
except ImportError:
    class EyeTracker: pass

try:
    from audio_monitor import AudioMonitor
except ImportError:
    class AudioMonitor: pass

try:
    from screen_monitor import ScreenMonitor
except ImportError:
    class ScreenMonitor: pass

try:
    from alert_system import AlertSystem
except ImportError:
    class AlertSystem: pass

try:
    from report_generator import ReportGenerator
except ImportError:
    class ReportGenerator: pass

try:
    from student_registration import StudentRegistration
except ImportError:
    class StudentRegistration: pass

try:
    from sms_service import SMSService
except ImportError:
    class SMSService: pass

try:
    from auto_grader import AutoGrader
except ImportError:
    class AutoGrader: pass

from email_service import mail, EmailService
from api import api
from auth.authentication import AuthenticationManager, SessionManager, PasswordManager
from utils.error_handlers import register_error_handlers
from security import SecurityUtils, block_automation, verify_exam_device
from functools import wraps
import threading
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
import json
import os

app = Flask(__name__)

@app.after_request
def add_ngrok_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    # Allow GeoGebra iframe loading
    response.headers['Content-Security-Policy'] = (
        "frame-src 'self' https://www.geogebra.org https://*.geogebra.org;"
    )
    return response

app.config.from_object(get_config())

db.init_app(app)
migrate = Migrate(app, db)
mail.init_app(app)
# csrf = CSRFProtect(app)
app.register_blueprint(api)

Config.init_app(app)

# Exempt JSON API endpoints from CSRF
API_ROUTES = [
    'start_exam', 'end_exam', 'submit_answer', 'proctoring_alert',
    'tab_switch', 'window_event', 'upload_snapshot', 'process_snapshot',
    'request_help', 'camera_issue', 'bulk_import_progress_stream',
    'delete_student', 'delete_cohort', 'delete_all_students',
    'delete_question', 'delete_exam', 'delete_exam_by_name',
    'grade_essay', 'flag_session', 'approve_admin', 'reject_admin',
    'deactivate_invigilator'
]

for route_name in API_ROUTES:
    view = app.view_functions.get(route_name)
    if view:
        csrf.exempt(view)

from sqlalchemy import event
import re

def is_sqlite(uri):
    return uri.startswith('sqlite://')

with app.app_context():
    if is_sqlite(app.config.get('SQLALCHEMY_DATABASE_URI', '')):
        @event.listens_for(db.engine, "connect")
        def sqlite_on_connect(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

auth_manager = AuthenticationManager()
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

import json
import secrets

@app.template_filter('from_json')
def from_json_filter(s):
    return json.loads(s) if s else {}

@app.template_global('csrf_token')
def csrf_token():
    """Generate CSRF token for templates"""
    from flask import session
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

face_detector = FaceDetector()
eye_tracker = EyeTracker()
audio_monitor = AudioMonitor()
screen_monitor = ScreenMonitor()
alert_system = AlertSystem()
report_generator = ReportGenerator()
student_registration = StudentRegistration()
sms_service = SMSService()
auto_grader = AutoGrader()

def on_audio_alert(session_id, event):
    with app.app_context():
        alert_system.audio_alert_callback(session_id, event)

def on_screen_alert(session_id, event, count):
    with app.app_context():
        alert_system.screen_alert_callback(session_id, event, count)

def login_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = flask_session.get('user_id')
            user_role = flask_session.get('role')
            if not user_id or user_role != role:
                return redirect(url_for('login', role=role))
            last_activity = flask_session.get('last_activity')
            if last_activity:
                try:
                    last_activity_dt = datetime.fromisoformat(last_activity)
                    if datetime.now() - last_activity_dt > timedelta(hours=1):
                        flask_session.clear()
                        return redirect(url_for('login', role=role))
                except ValueError:
                    flask_session.clear()
                    return redirect(url_for('login', role=role))
            flask_session['last_activity'] = datetime.now().isoformat()
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flask_session.get('role') != 'admin' or not flask_session.get('admin_id'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flask_session.get('role') != 'admin' or not flask_session.get('is_super_admin'):
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_invigilator_cohorts():
    inv_id = flask_session.get('user_id')
    if not inv_id or flask_session.get('role') != 'invigilator':
        return []
    invigilator = Invigilator.query.get(inv_id)
    if not invigilator or not invigilator.assigned_cohorts:
        return None
    return invigilator.cohort_list

def get_current_institution_id():
    role = flask_session.get('role')
    if role == 'admin':
        admin = Admin.query.get(flask_session.get('admin_id'))
        return admin.institution_id if admin else None
    elif role == 'invigilator':
        inv = Invigilator.query.get(flask_session.get('user_id'))
        return inv.institution_id if inv else None
    elif role == 'student':
        student = Student.query.get(flask_session.get('user_id'))
        return student.institution_id if student else None
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat(), 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'timestamp': datetime.utcnow().isoformat(), 'database': 'disconnected'}), 500

@app.route('/login/<role>', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def login(role):
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if role == 'invigilator':
            user = Invigilator.query.filter_by(email=email).first()
            if user and user.check_password(password):
                if hasattr(user, 'is_active') and not user.is_active:
                    return render_template('login.html', role=role, error='Account deactivated')
                SessionManager.create_session(str(user.id), 'invigilator')
                flask_session['user_id'] = user.id
                flask_session['role'] = 'invigilator'
                flask_session['name'] = user.name
                return redirect(url_for('invigilator_dashboard'))
        else:
            user = Student.query.filter_by(email=email).first()
            if user and user.check_password(password):
                SessionManager.create_session(str(user.id), 'student')
                flask_session['user_id'] = user.id
                flask_session['role'] = role
                flask_session['name'] = user.name
                return redirect(url_for('student_dashboard'))
        return render_template('login.html', role=role, error='Invalid credentials')
    return render_template('login.html', role=role)

@app.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        invigilator = Invigilator.query.filter_by(email=email).first()
        if invigilator:
            import secrets
            reset_token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(hours=1)
            invigilator.reset_token = reset_token
            invigilator.reset_token_expiry = expiry
            db.session.commit()
            reset_link = request.host_url.rstrip('/') + url_for('reset_password', token=reset_token)
            try:
                email_service = EmailService()
                email_service.send_password_reset(invigilator.email, invigilator.name, reset_link)
                success_msg = f"Password reset link sent to {email}. Please check your inbox."
            except Exception as e:
                success_msg = f"Reset link generated (email not configured): {reset_link}"
            return render_template('forgot_password.html', success=success_msg)
        else:
            return render_template('forgot_password.html', success=f"If {email} is registered, you will receive a reset link shortly.")
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def reset_password(token):
    invigilator = Invigilator.query.filter_by(reset_token=token).first()
    if not invigilator or not invigilator.reset_token_expiry:
        return render_template('forgot_password.html', error='Invalid or expired reset link.')
    if datetime.utcnow() > invigilator.reset_token_expiry:
        invigilator.reset_token = None
        invigilator.reset_token_expiry = None
        db.session.commit()
        return render_template('forgot_password.html', error='Reset link has expired.')
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            return render_template('forgot_password.html', error='Passwords do not match!')
        if len(password) < 6:
            return render_template('forgot_password.html', error='Password must be at least 6 characters.')
        invigilator.set_password(password)
        invigilator.reset_token = None
        invigilator.reset_token_expiry = None
        db.session.commit()
        return render_template('login.html', role='invigilator', success='Password reset successful!')
    return render_template('reset_password.html', token=token)

@app.route('/logout')
def logout():
    SessionManager.destroy_session()
    flask_session.clear()
    return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = Admin.query.filter_by(email=email, is_active=True).first()
        if admin and admin.check_password(password):
            flask_session['admin_id'] = admin.id
            flask_session['name'] = admin.name
            flask_session['role'] = 'admin'
            flask_session['is_super_admin'] = (admin.id == 1)
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def admin_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        institution_name = request.form.get('institution_name')
        if len(password) < 8:
            return render_template('admin_register.html', error='Password must be at least 8 characters')
        if Admin.query.filter_by(email=email).first():
            return render_template('admin_register.html', error='Email already exists')
        admin = Admin(name=name, email=email, institution_name=institution_name, is_active=False)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        return render_template('admin_register.html', success='Registration submitted! Your account will be activated once approved by our team.')
    return render_template('admin_register.html')

@app.route('/admin/logout')
def admin_logout():
    flask_session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/change_password', methods=['GET', 'POST'])
@admin_required
def admin_change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        admin = Admin.query.get(flask_session['admin_id'])
        
        if not admin.check_password(current_password):
            return render_template('admin_change_password.html', error='Current password is incorrect')
        
        if new_password != confirm_password:
            return render_template('admin_change_password.html', error='New passwords do not match')
        
        if len(new_password) < 8:
            return render_template('admin_change_password.html', error='Password must be at least 8 characters')
        
        admin.set_password(new_password)
        db.session.commit()
        
        return render_template('admin_change_password.html', success='Password changed successfully!')
    
    return render_template('admin_change_password.html')



@app.route('/invigilator/dashboard')
@login_required('invigilator')
def invigilator_dashboard():
    active_sessions = ExamSession.query.filter_by(status='in_progress').all()
    recent_alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(10).all()
    all_students = Student.query.all()
    cohorts = sorted(set(s.cohort for s in all_students if s.cohort))
    return render_template('invigilator_dashboard.html',
                         active_sessions=active_sessions,
                         alerts=recent_alerts,
                         all_students=all_students,
                         cohorts=cohorts,
                         flask_session=flask_session,
                         now=datetime.utcnow())

@app.route('/student/dashboard')
@login_required('student')
def student_dashboard():
    student = Student.query.get(flask_session['user_id'])
    active_exam = ExamSession.query.filter_by(student_id=student.id, status='in_progress').first()
    expired_message = None
    if active_exam and active_exam.scheduled_start and active_exam.duration_minutes:
        exam_end_time = active_exam.start_time + timedelta(minutes=active_exam.duration_minutes)
        if datetime.utcnow() > exam_end_time:
            active_exam.status = 'failed'
            active_exam.end_time = exam_end_time
            db.session.commit()
            expired_message = f'Your exam "{active_exam.exam_name}" has expired.'
            active_exam = None
    
    all_scheduled = ExamSession.query.filter_by(student_id=student.id, status='scheduled').all()
    scheduled_exams = []
    for exam in all_scheduled:
        if exam.scheduled_start and exam.duration_minutes:
            exam_end_time = exam.scheduled_start + timedelta(minutes=exam.duration_minutes)
            if datetime.utcnow() > exam_end_time:
                exam.status = 'failed'
                db.session.commit()
            else:
                scheduled_exams.append(exam)
        else:
            scheduled_exams.append(exam)
    
    past_exams = ExamSession.query.filter_by(student_id=student.id).filter(
        ExamSession.status.in_(['completed', 'failed'])).order_by(ExamSession.start_time.desc()).all()
    return render_template('student_dashboard.html',
                         student=student,
                         past_exams=past_exams,
                         scheduled_exams=scheduled_exams,
                         active_exam=active_exam,
                         expired_message=expired_message,
                         now=lambda: datetime.utcnow())

@app.route('/student/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def student_register():
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        photo = request.files.get('photo')
        if Student.query.filter_by(email=email).first():
            return render_template('student_register.html', error='Email already exists')
        student, message = student_registration.register_student(name, student_id, email, photo, password)
        if student:
            student.set_password(password)
            student.email_verified = True
            db.session.commit()
            return redirect(url_for('login', role='student'))
        return render_template('student_register.html', error=message)
    return render_template('student_register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if 'user_id' not in flask_session or flask_session.get('role') != 'invigilator':
            return redirect(url_for('login', role='invigilator'))
        return render_template('register.html', flask_session=flask_session)
    if 'user_id' not in flask_session or flask_session.get('role') != 'invigilator':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    name = request.form.get('name')
    student_id = request.form.get('student_id')
    email = request.form.get('email')
    password = request.form.get('password')
    photo = request.files.get('photo')
    if Student.query.filter_by(student_id=student_id).first():
        return jsonify({'success': False, 'message': 'Student ID already exists'})
    if Student.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already exists'})
    student, message = student_registration.register_student(name, student_id, email, photo, password)
    if student:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'message': message})

@app.route('/students')
@login_required('invigilator')
def students():
    institution_id = get_current_institution_id()
    cohorts_filter = get_current_invigilator_cohorts()
    
    if institution_id:
        if cohorts_filter is not None and len(cohorts_filter) > 0:
            all_students = Student.query.filter(
                Student.institution_id == institution_id,
                Student.cohort.in_(cohorts_filter)
            ).all()
        else:
            all_students = Student.query.filter_by(institution_id=institution_id).all()
    else:
        all_students = student_registration.get_all_students()
    
    from collections import defaultdict
    cohorts = defaultdict(list)
    for student in all_students:
        cohorts[student.cohort or 'Uncategorized'].append(student)
    return render_template('students.html', cohorts=dict(sorted(cohorts.items())))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required('invigilator')
def delete_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'})
    ExamSession.query.filter_by(student_id=student_id).delete()
    db.session.delete(student)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete_cohort', methods=['POST'])
@login_required('invigilator')
def delete_cohort():
    cohort = request.json.get('cohort')
    students = Student.query.filter_by(cohort=cohort).all()
    for student in students:
        for exam_session in ExamSession.query.filter_by(student_id=student.id).all():
            Alert.query.filter_by(session_id=exam_session.id).delete()
        ExamSession.query.filter_by(student_id=student.id).delete()
        db.session.delete(student)
    db.session.commit()
    return jsonify({'success': True, 'count': len(students)})

@app.route('/delete_all_students', methods=['POST'])
@login_required('invigilator')
def delete_all_students():
    try:
        count = Student.query.count()
        Answer.query.delete()
        Alert.query.delete()
        ExamSession.query.delete()
        Student.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/exam/<student_id>')
@login_required('student')
def exam(student_id):
    student = Student.query.get(flask_session['user_id'])
    if not student or student.student_id != student_id:
        return "Unauthorized", 403
    session_id = request.args.get('session_id')
    exam_session = None
    is_resume = False
    questions = []
    if session_id:
        exam_session = ExamSession.query.get(session_id)
        if exam_session:
            if exam_session.status == 'in_progress':
                is_resume = True
            questions = Question.query.filter_by(exam_name=exam_session.exam_name).order_by(Question.order).all()
    return render_template('exam.html', student=student, exam_session=exam_session, is_resume=is_resume, questions=questions)

@app.route('/submit_answer', methods=['POST'])
@login_required('student')
@verify_exam_device
def submit_answer():
    data = request.json
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    answer_text = data.get('answer_text')
    existing = Answer.query.filter_by(session_id=session_id, question_id=question_id).first()
    if existing:
        existing.answer_text = answer_text
        existing.submitted_at = datetime.utcnow()
    else:
        answer = Answer(session_id=session_id, question_id=question_id, answer_text=answer_text)
        db.session.add(answer)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/start_exam', methods=['POST'])
@block_automation
def start_exam():
    data = request.json
    student_id = data.get('student_id')
    exam_name = data.get('exam_name')

    student = student_registration.get_student(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'})

    # Check institution session limit
    if student.institution_id:
        institution = Institution.query.get(student.institution_id)
        if institution and institution.is_over_limit:
            return jsonify({'success': False, 'message': 'Institution session limit reached. Please contact your administrator.'})

    existing_session = ExamSession.query.filter_by(
        student_id=student.id, exam_name=exam_name, status='completed').first()
    if existing_session:
        return jsonify({'success': False, 'message': 'You have already completed this exam.'})

    active_session = ExamSession.query.filter_by(
        student_id=student.id, exam_name=exam_name, status='in_progress').first()
    if active_session:
        return jsonify({'success': True, 'session_id': active_session.id})

    scheduled_session = ExamSession.query.filter_by(
        student_id=student.id, exam_name=exam_name, status='scheduled').first()
    
    if scheduled_session:
        scheduled_session.status = 'in_progress'
        scheduled_session.start_time = datetime.utcnow()
        session = scheduled_session
    else:
        session = ExamSession(
            student_id=student.id,
            institution_id=student.institution_id,
            exam_name=exam_name,
            status='in_progress',
            start_time=datetime.utcnow()
        )
        db.session.add(session)
    
    db.session.commit()
    
    # Increment institution session counter
    if student.institution_id:
        institution = Institution.query.get(student.institution_id)
        if institution:
            institution.sessions_used_this_month += 1
            db.session.commit()
    
    inv = Invigilator.query.join(Student).filter(Student.id == student.id).first()
    if not inv:
        inv = Invigilator.query.filter(Invigilator.assigned_cohorts.like(f'%{student.cohort}%')).first()
    if inv and inv.admin_id:
        active_count = ExamSession.query.filter_by(exam_name=exam_name, status='in_progress').count()
        activity = ActivityLog(
            admin_id=inv.admin_id,
            activity_type='exam_started',
            description=f'Exam "{exam_name}" started - {active_count} students active',
            invigilator_id=inv.id,
            extra_data=f'{{"exam_name": "{exam_name}", "active_count": {active_count}}}'
        )
        db.session.add(activity)
        db.session.commit()

    SecurityUtils.bind_session_to_device()

    alert_system.register_session(session.id)
    audio_monitor.start_session(session.id, alert_callback=on_audio_alert)
    screen_monitor.start_session(session.id, alert_callback=on_screen_alert)

    return jsonify({'success': True, 'session_id': session.id})

@app.route('/end_exam', methods=['POST'])
@block_automation
@verify_exam_device
def end_exam():
    session_id = request.json.get('session_id') if request.json else None
    is_auto_submit = request.json.get('is_auto_submit', False) if request.json else False

    if not session_id:
        return jsonify({'success': False, 'message': 'No session ID'})

    session = ExamSession.query.get(session_id)
    if session:
        session.end_time = datetime.utcnow()
        session.status = 'completed'
        session.is_auto_submitted = is_auto_submit
        db.session.commit()

        grading_result = auto_grader.grade_session(session_id)

        if is_auto_submit:
            alert = Alert(
                session_id=session_id,
                alert_type='auto_submit',
                severity='high',
                description=f'Exam auto-submitted due to time expiry. Student: {session.student.name}, Exam: {session.exam_name}'
            )
            db.session.add(alert)
            db.session.commit()

    audio_monitor.stop_session(session_id)
    screen_monitor.stop_session(session_id)
    alert_system.clear_session(session_id)

    return jsonify({'success': True, 'session_id': session_id})

@app.route('/get_snapshot/<int:session_id>')
@login_required('invigilator')
def get_snapshot(session_id):
    from flask import send_file
    filepath = os.path.join('static', 'snapshots', f'session_{session_id}_latest.jpg')
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/jpeg')
    return '', 404

@app.route('/api/recent_alerts')
@limiter.exempt
@login_required('invigilator')
def recent_alerts():
    alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(10).all()
    alerts_data = []
    for alert in alerts:
        alert_dict = {
            'alert_type': alert.alert_type,
            'description': alert.description,
            'severity': alert.severity,
            'time': alert.timestamp.strftime('%H:%M'),
            'session': None
        }
        if alert.session and alert.session.student:
            alert_dict['session'] = {'student': {'name': alert.session.student.name}}
        alerts_data.append(alert_dict)
    return jsonify({'alerts': alerts_data})

@app.route('/report/<int:session_id>')
def report(session_id):
    report_data = report_generator.generate_session_report(session_id)
    if not report_data:
        return "Report not found", 404
    return render_template('report.html', report=report_data)

@app.route('/report/<int:session_id>/pdf')
def report_pdf(session_id):
    pdf_buffer = report_generator.generate_pdf_report(session_id)
    if not pdf_buffer:
        return "Report not found", 404
    return Response(pdf_buffer.getvalue(), mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename=exam_report_{session_id}.pdf'})

@app.route('/admin/reports')
@admin_required
def admin_reports():
    admin = Admin.query.get(flask_session['admin_id'])
    invigilators = Invigilator.query.filter_by(admin_id=admin.id).all()
    cohorts = []
    for inv in invigilators:
        if inv.assigned_cohorts:
            cohorts.extend(inv.cohort_list)
    
    student_ids = [s.id for s in Student.query.filter(
        Student.cohort.in_(cohorts)).all()] if cohorts else []
    
    sessions = ExamSession.query.filter(
        ExamSession.student_id.in_(student_ids)
    ).order_by(ExamSession.start_time.desc()).all()
    
    grouped = {}
    for inv in invigilators:
        inv_cohorts = inv.cohort_list if inv.assigned_cohorts else []
        inv_student_ids = [s.id for s in Student.query.filter(
            Student.cohort.in_(inv_cohorts)).all()]
        grouped[inv.name] = [s for s in sessions if s.student_id in inv_student_ids]
    
    return render_template('admin_reports.html', grouped=grouped, invigilators=invigilators, admin=admin)

@app.route('/super/reports')
@super_admin_required
def super_reports():
    institutions = Institution.query.all()
    report_data = []
    for inst in institutions:
        inst_sessions = ExamSession.query.join(Student).filter(
            Student.institution_id == inst.id).all()
        report_data.append({
            'institution': inst.name,
            'total_sessions': len(inst_sessions),
            'completed': sum(1 for s in inst_sessions if s.status == 'completed'),
            'in_progress': sum(1 for s in inst_sessions if s.status == 'in_progress'),
            'avg_score': sum(s.total_score or 0 for s in inst_sessions) / max(len(inst_sessions), 1),
            'total_alerts': sum(Alert.query.filter_by(session_id=s.id).count() for s in inst_sessions)
        })
    
    return render_template('super_reports.html', report_data=report_data)

@app.route('/sessions')
@login_required('invigilator')
def sessions():
    all_sessions = ExamSession.query.order_by(ExamSession.start_time.desc()).all()
    cohorts = sorted(set(s.student.cohort for s in all_sessions if s.student and s.student.cohort))
    return render_template('sessions.html', sessions=all_sessions, cohorts=cohorts)

@app.route('/export_results/<cohort>')
@login_required('invigilator')
def export_results(cohort):
    students = Student.query.filter_by(cohort=cohort).all()
    student_ids = [s.id for s in students]
    sessions = ExamSession.query.filter(
        ExamSession.student_id.in_(student_ids), ExamSession.status == 'completed').all()
    ungraded_count = 0
    for session in sessions:
        questions = Question.query.filter_by(exam_name=session.exam_name).all()
        answers = Answer.query.filter_by(session_id=session.id).all()
        answer_dict = {a.question_id: a for a in answers}
        for q in questions:
            if q.question_type == 'essay' and answer_dict.get(q.id) and not answer_dict[q.id].graded_at:
                ungraded_count += 1
    if ungraded_count > 0:
        return f"Cannot export: {ungraded_count} essay(s) need grading first.", 400
    data = []
    for session in sessions:
        results = auto_grader.get_session_results(session.id)
        data.append({
            'Student Name': session.student.name,
            'Student ID': session.student.student_id,
            'Email': session.student.email,
            'Exam Name': session.exam_name,
            'Start Time': session.start_time.strftime('%Y-%m-%d %H:%M') if session.start_time else '',
            'End Time': session.end_time.strftime('%Y-%m-%d %H:%M') if session.end_time else '',
            'Score': results.get('total_score', 0),
            'Max Score': results.get('max_score', 0),
            'Percentage': f"{results.get('percentage', 0):.1f}%",
            'Status': session.status,
            'Alerts': Alert.query.filter_by(session_id=session.id).count()
        })
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
    output.seek(0)
    return Response(output.getvalue(),
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': f'attachment; filename={cohort}_results.xlsx'})

@app.route('/alerts')
@login_required('invigilator')
def alerts():
    all_alerts = Alert.query.order_by(Alert.timestamp.desc()).all()
    return render_template('alerts.html', alerts=all_alerts, flask_session=flask_session)

@app.route('/exam_schedule')
@login_required('invigilator')
def exam_schedule():
    all_scheduled = ExamSession.query.filter(ExamSession.student_id.isnot(None)).all()
    from collections import defaultdict
    exams_grouped = defaultdict(list)
    for exam in all_scheduled:
        if exam.student:
            exams_grouped[exam.exam_name].append(exam)
    return render_template('exam_schedule.html', exams_grouped=dict(exams_grouped), flask_session=flask_session)

@app.route('/bulk_import', methods=['GET', 'POST'])
@login_required('invigilator')
def bulk_import():
    if request.method == 'POST':
        import uuid
        import queue as _queue
        import threading
        
        if not hasattr(app, 'bulk_import_progress'):
            app.bulk_import_progress = {}
        
        file = request.files.get('csv_file')
        notify_email = request.form.get('notify_email')
        
        if not file:
            return render_template('bulk_import.html', error='No file uploaded', flask_session=flask_session)
        
        filename = file.filename.lower()
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return render_template('bulk_import.html', error='Only CSV and Excel files are supported', flask_session=flask_session)
        except Exception as e:
            return render_template('bulk_import.html', error=f'Error reading file: {str(e)}', flask_session=flask_session)
        
        required_cols = ['name', 'student_id', 'email']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            return render_template('bulk_import.html', error=f'Missing columns: {", ".join(missing_cols)}', flask_session=flask_session)
        
        job_id = str(uuid.uuid4())
        progress_q = _queue.Queue()
        app.bulk_import_progress[job_id] = progress_q
        
        inst_id = get_current_institution_id()
        
        def _run_import():
            with app.app_context():
                CHUNK_SIZE = 200
                rows = list(df.iterrows())
                total = len(rows)
                imported = 0
                skipped = 0
                skipped_list = []
                credentials = []
                
                progress_q.put({'phase': 'validating', 'pct': 0, 'msg': f'Validating {total} rows...'})
                
                existing_ids = {s.student_id for s in Student.query.with_entities(Student.student_id).all()}
                existing_emails = {s.email for s in Student.query.with_entities(Student.email).all()}
                
                batch = []
                for idx, (_, row) in enumerate(rows):
                    sid = str(row.get('student_id', '')).strip()
                    email = str(row.get('email', '')).strip()
                    name = str(row.get('name', '')).strip()
                    
                    if not sid or not email or not name:
                        skipped += 1
                        skipped_list.append(f"Row {idx+2}: missing required field")
                        continue
                    
                    if sid in existing_ids or email in existing_emails:
                        skipped += 1
                        skipped_list.append(f"{name} ({sid}) - already exists")
                        continue
                    
                    password = sid
                    s = Student(
                        name=name,
                        student_id=sid,
                        email=email,
                        cohort=str(row.get('cohort', 'Default')).strip(),
                        email_verified=True,
                        institution_id=inst_id
                    )
                    s.set_password(password)
                    batch.append(s)
                    credentials.append({'name': name, 'student_id': sid, 'email': email, 'password': password})
                    existing_ids.add(sid)
                    existing_emails.add(email)
                    
                    if idx % 50 == 0:
                        pct = int((idx / total) * 40)
                        progress_q.put({'phase': 'validating', 'pct': pct, 'msg': f'Validated {idx}/{total}...'})
                
                total_to_insert = len(batch)
                progress_q.put({'phase': 'importing', 'pct': 40, 'msg': f'Inserting {total_to_insert} students...'})
                
                for chunk_start in range(0, total_to_insert, CHUNK_SIZE):
                    chunk = batch[chunk_start:chunk_start + CHUNK_SIZE]
                    try:
                        db.session.bulk_save_objects(chunk)
                        db.session.commit()
                        imported += len(chunk)
                    except Exception as e:
                        db.session.rollback()
                        skipped += len(chunk)
                        skipped_list.append(f"Chunk error: {str(e)}")
                    
                    pct = 40 + int((imported / max(total_to_insert, 1)) * 55)
                    progress_q.put({'phase': 'importing', 'pct': pct, 'msg': f'Imported {imported}/{total_to_insert}...'})
                    time.sleep(0.05)
                
                if notify_email and imported > 0:
                    try:
                        email_service = EmailService()
                        body = f'<h2>Bulk Import Complete</h2><p>Imported: {imported}<br>Skipped: {skipped}</p>'
                        email_service.send_email(notify_email, f'Bulk Import - {imported} Students Added', body)
                    except:
                        pass
                
                progress_q.put({
                    'phase': 'done',
                    'pct': 100,
                    'msg': f'Done! {imported} imported, {skipped} skipped.',
                    'imported': imported,
                    'skipped': skipped,
                    'skipped_list': skipped_list[:30],
                    'credentials': credentials[:50]
                })
        
        t = threading.Thread(target=_run_import, daemon=True)
        t.start()
        
        return render_template('bulk_import.html', job_id=job_id, total_rows=len(df), flask_session=flask_session)
    
    return render_template('bulk_import.html', flask_session=flask_session)

@app.route('/bulk_import/progress/<job_id>')
@login_required('invigilator')
def bulk_import_progress_stream(job_id):
    import queue as _queue
    import json
    
    def _stream():
        if not hasattr(app, 'bulk_import_progress'):
            yield "data: {\"error\": \"Job not found\"}\n\n"
            return
        
        q = app.bulk_import_progress.get(job_id)
        if not q:
            yield "data: {\"error\": \"Job not found\"}\n\n"
            return
        
        while True:
            try:
                update = q.get(timeout=30)
                yield f"data: {json.dumps(update)}\n\n"
                if update.get('phase') == 'done':
                    app.bulk_import_progress.pop(job_id, None)
                    break
            except _queue.Empty:
                yield "data: {\"phase\": \"heartbeat\"}\n\n"
    
    return Response(_stream(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/manage_questions/<exam_name>', methods=['GET', 'POST'])
@login_required('invigilator')
def manage_questions(exam_name):
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        question_type = request.form.get('question_type')
        points = int(request.form.get('points', 1))
        allow_calculator = request.form.get('allow_calculator') == '1'
        programming_language = request.form.get('programming_language', 'python')
        
        # Map question type to subtype for code questions
        question_subtype = None
        if question_type == 'code' and programming_language:
            question_subtype = f'code_{programming_language}'
        
        # Handle graph reference image and axis config
        reference_image = None
        graph_config = None
        if question_type == 'graph':
            reference_image = request.form.get('graph_reference_image')
            # Build axis configuration
            x_min = request.form.get('graph_x_min', '-10')
            x_max = request.form.get('graph_x_max', '10')
            y_min = request.form.get('graph_y_min', '-10')
            y_max = request.form.get('graph_y_max', '10')
            step = request.form.get('graph_step', '1')
            graph_config = {
                'x_min': float(x_min),
                'x_max': float(x_max),
                'y_min': float(y_min),
                'y_max': float(y_max),
                'step': float(step)
            }
        
        question = Question(
            exam_name=exam_name, question_text=question_text,
            question_type=question_type, points=points,
            allow_calculator=allow_calculator,
            question_subtype=question_subtype,
            programming_language=programming_language if question_type == 'code' else None,
            reference_image=reference_image if question_type == 'graph' else None,
            options=json.dumps(graph_config) if graph_config else None,
            order=Question.query.filter_by(exam_name=exam_name).count() + 1)
        if question_type == 'multiple_choice':
            options = {'A': request.form.get('option_a'), 'B': request.form.get('option_b'),
                       'C': request.form.get('option_c'), 'D': request.form.get('option_d')}
            question.options = json.dumps(options)
            question.correct_answer = request.form.get('correct_answer')
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('manage_questions', exam_name=exam_name))
    questions = Question.query.filter_by(exam_name=exam_name).order_by(Question.order).all()
    return render_template('manage_questions.html', exam_name=exam_name, questions=questions, flask_session=flask_session)

@app.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required('invigilator')
def delete_question(question_id):
    question = Question.query.get(question_id)
    if question:
        db.session.delete(question)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/view_answers/<int:session_id>')
@login_required('invigilator')
def view_answers(session_id):
    session = ExamSession.query.get(session_id)
    if not session:
        return "Session not found", 404
    results = auto_grader.get_session_results(session_id)
    questions = Question.query.filter_by(exam_name=session.exam_name).order_by(Question.order).all()
    answers = {a.question_id: a for a in Answer.query.filter_by(session_id=session_id).all()}
    needs_grading = any(q.question_type == 'essay' and answers.get(q.id) and not answers[q.id].graded_at for q in questions)
    return render_template('view_answers.html', session=session, questions=questions,
                         answers=answers, results=results, needs_grading=needs_grading,
                         flask_session=flask_session)

@app.route('/grade_essay', methods=['POST'])
@login_required('invigilator')
def grade_essay():
    answer_id = request.json.get('answer_id')
    points = int(request.json.get('points'))
    feedback = request.json.get('feedback', '')
    answer = Answer.query.get(answer_id)
    if not answer:
        return jsonify({'success': False, 'message': 'Answer not found'})
    answer.points_earned = points
    answer.grading_feedback = feedback
    answer.graded_by = flask_session['user_id']
    answer.graded_at = datetime.utcnow()
    session = ExamSession.query.get(answer.session_id)
    all_answers = Answer.query.filter_by(session_id=answer.session_id).all()
    session.total_score = sum(a.points_earned for a in all_answers)
    db.session.commit()
    return jsonify({'success': True, 'total_score': session.total_score})

@app.route('/delete_exam/<int:exam_id>', methods=['POST'])
@login_required('invigilator')
def delete_exam(exam_id):
    exam = ExamSession.query.get(exam_id)
    if exam:
        Answer.query.filter_by(session_id=exam_id).delete()
        Alert.query.filter_by(session_id=exam_id).delete()
        db.session.delete(exam)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/delete_exam_by_name', methods=['POST'])
@login_required('invigilator')
def delete_exam_by_name():
    exam_name = request.json.get('exam_name')
    exams = ExamSession.query.filter_by(exam_name=exam_name, status='scheduled').all()
    for exam in exams:
        Answer.query.filter_by(session_id=exam.id).delete()
        Alert.query.filter_by(session_id=exam.id).delete()
        db.session.delete(exam)
    db.session.commit()
    return jsonify({'success': True, 'count': len(exams)})

@app.route('/schedule_exam', methods=['POST'])
@login_required('invigilator')
def schedule_exam():
    cohort = request.form.get('cohort')
    student_id = request.form.get('student_id')
    exam_name = request.form.get('exam_name')
    naive_dt = datetime.fromisoformat(request.form.get('scheduled_start'))
    scheduled_start = LOCAL_TZ.localize(naive_dt).astimezone(pytz.utc).replace(tzinfo=None)
    duration_minutes = int(request.form.get('duration_minutes'))
    if not cohort:
        return "Cohort is required", 400
    student_count = 0
    if student_id:
        session = ExamSession(student_id=student_id, exam_name=exam_name,
                              scheduled_start=scheduled_start, duration_minutes=duration_minutes, status='scheduled')
        db.session.add(session)
        student_count = 1
    else:
        students = Student.query.filter_by(cohort=cohort).all()
        if not students:
            return f"No students found in cohort '{cohort}'", 400
        student_count = len(students)
        for student in students:
            session = ExamSession(student_id=student.id, exam_name=exam_name,
                                  scheduled_start=scheduled_start, duration_minutes=duration_minutes, status='scheduled')
            db.session.add(session)
    db.session.commit()
    inv = Invigilator.query.get(flask_session['user_id'])
    if inv and inv.admin_id:
        activity = ActivityLog(
            admin_id=inv.admin_id,
            activity_type='exam_scheduled',
            description=f'{inv.name} scheduled "{exam_name}" for {student_count} students in {cohort}',
            invigilator_id=inv.id,
            extra_data=f'{{"exam_name": "{exam_name}", "cohort": "{cohort}", "student_count": {student_count}}}'
        )
        db.session.add(activity)
        db.session.commit()
    return redirect(url_for('invigilator_dashboard'))

@app.route('/live_review')
@login_required('invigilator')
def live_review():
    active_sessions = ExamSession.query.filter_by(status='in_progress').all()
    recent_alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(50).all()
    return render_template('live_review.html', active_sessions=active_sessions, alerts=recent_alerts, now=datetime.utcnow())

@app.route('/flag_session/<int:session_id>', methods=['POST'])
@login_required('invigilator')
def flag_session(session_id):
    alert = Alert(session_id=session_id, alert_type='manual_flag', severity='high',
                  description='Session flagged by invigilator for review')
    db.session.add(alert)
    db.session.commit()
    return jsonify({'success': True})

@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f'404 error: {request.url}')
    return render_template('error.html', code=404, message='Page not found'), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f'500 error: {str(e)}', exc_info=True)
    return render_template('error.html', code=500, message='Server error'), 500

@app.errorhandler(403)
def forbidden(e):
    app.logger.warning(f'403 error: {request.url}')
    return render_template('error.html', code=403, message='Access denied'), 403

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled exception: {str(e)}', exc_info=True)
    return render_template('error.html', code=500, message='An unexpected error occurred'), 500

@app.route('/verify_email/<token>')
def verify_email(token):
    student = Student.query.filter_by(verification_token=token).first()
    if not student:
        return render_template('error.html', code=400, message='Invalid verification link')
    if student.email_verified:
        return redirect(url_for('login', role='student'))
    student.email_verified = True
    student.verification_token = None
    db.session.commit()
    return render_template('verify_success.html')

@app.route('/embed/exam/<int:session_id>')
def embed_exam(session_id):
    return render_template('embed_exam.html', session_id=session_id)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    admin = Admin.query.get(flask_session['admin_id'])
    is_super_admin = flask_session.get('is_super_admin', False)
    invigilators = Invigilator.query.filter_by(admin_id=admin.id).all()
    
    # Get students only from this admin's invigilators' cohorts
    cohorts = []
    for inv in invigilators:
        if inv.assigned_cohorts:
            cohorts.extend(inv.cohort_list)
    
    if cohorts:
        total_students = Student.query.filter(Student.cohort.in_(cohorts)).count()
        student_ids = [s.id for s in Student.query.filter(Student.cohort.in_(cohorts)).all()]
        total_exams = ExamSession.query.filter(ExamSession.student_id.in_(student_ids)).count()
        active_sessions = ExamSession.query.filter(ExamSession.student_id.in_(student_ids), ExamSession.status=='in_progress').count()
    else:
        total_students = 0
        total_exams = 0
        active_sessions = 0
    
    pending_admins = Admin.query.filter_by(is_active=False).all() if is_super_admin else []
    recent_activities = ActivityLog.query.filter_by(admin_id=admin.id).order_by(ActivityLog.timestamp.desc()).limit(15).all()
    return render_template('admin_dashboard.html', admin=admin, invigilators=invigilators,
                         total_students=total_students, total_exams=total_exams, 
                         active_sessions=active_sessions, is_super_admin=is_super_admin,
                         pending_admins=pending_admins, recent_activities=recent_activities)

@app.route('/admin/approve/<int:admin_id>', methods=['POST'])
@admin_required
def approve_admin(admin_id):
    if not flask_session.get('is_super_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    admin = Admin.query.get_or_404(admin_id)
    admin.is_active = True
    db.session.commit()
    try:
        email_service = EmailService()
        body = f'''<h2>Account Approved</h2>
<p>Hello {admin.name},</p>
<p>Your admin account for {admin.institution_name} has been approved!</p>
<p>You can now login at: <a href="{request.host_url}admin/login">{request.host_url}admin/login</a></p>'''
        email_service.send_email(admin.email, 'Admin Account Approved - AI Invigilator', body)
    except Exception as e:
        print(f"Email notification failed: {e}")
    return jsonify({'success': True})

@app.route('/admin/reject/<int:admin_id>', methods=['POST'])
@admin_required
def reject_admin(admin_id):
    if not flask_session.get('is_super_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    admin = Admin.query.get_or_404(admin_id)
    db.session.delete(admin)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/create_invigilator', methods=['GET', 'POST'])
@admin_required
def create_invigilator():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        cohorts = request.form.get('cohorts', '')
        if len(password) < 8:
            return render_template('create_invigilator.html', error='Password must be at least 8 characters')
        if Invigilator.query.filter_by(email=email).first():
            return render_template('create_invigilator.html', error='Email already exists')
        
        admin = Admin.query.get(flask_session['admin_id'])
        invigilator = Invigilator(
            name=name, 
            email=email, 
            admin_id=flask_session['admin_id'],
            institution_id=admin.institution_id
        )
        invigilator.set_password(password)
        invigilator.assigned_cohorts = cohorts
        db.session.add(invigilator)
        db.session.commit()
        try:
            email_service = EmailService()
            body = f'''<h2>Invigilator Account Created</h2>
<p>Hello {name},</p>
<p>Your invigilator account has been created by {admin.institution_name}.</p>
<p><strong>Login Credentials:</strong></p>
<ul>
<li>Email: {email}</li>
<li>Password: {password}</li>
</ul>
<p>Login at: <a href="{request.host_url}login/invigilator">{request.host_url}login/invigilator</a></p>
<p>Assigned Cohorts: {cohorts if cohorts else "None (All access)"}</p>
<p><strong>Important:</strong> Please change your password after first login.</p>'''
            email_service.send_email(email, 'Your Invigilator Account - AI Invigilator', body)
        except Exception as e:
            print(f"Email notification failed: {e}")
        return redirect(url_for('admin_dashboard'))
    return render_template('create_invigilator.html')

@app.route('/admin/edit_invigilator/<int:inv_id>', methods=['GET', 'POST'])
@admin_required
def edit_invigilator(inv_id):
    invigilator = Invigilator.query.get_or_404(inv_id)
    if invigilator.admin_id != flask_session['admin_id']:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        invigilator.name = request.form.get('name')
        invigilator.assigned_cohorts = request.form.get('cohorts', '')
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_invigilator.html', invigilator=invigilator)

@app.route('/admin/deactivate_invigilator/<int:inv_id>', methods=['POST'])
@admin_required
def deactivate_invigilator(inv_id):
    invigilator = Invigilator.query.get_or_404(inv_id)
    if invigilator.admin_id != flask_session['admin_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    invigilator.is_active = False
    db.session.commit()
    return jsonify({'success': True})

@app.route('/super/dashboard')
@super_admin_required
def super_dashboard():
    stats = {
        'total_institutions': Institution.query.count(),
        'total_students': Student.query.count(),
        'total_sessions': ExamSession.query.count(),
        'active_sessions': ExamSession.query.filter_by(status='in_progress').count()
    }
    recent_institutions = Institution.query.order_by(Institution.created_at.desc()).limit(10).all()
    pending_admins = Admin.query.filter_by(is_active=False).all()
    return render_template('super_dashboard.html', stats=stats, recent_institutions=recent_institutions, pending_admins=pending_admins)

@app.route('/super/institutions')
@super_admin_required
def super_institutions():
    institutions = Institution.query.order_by(Institution.name).all()
    return render_template('super_institutions.html', institutions=institutions)

@app.route('/super/institution/<int:inst_id>', methods=['GET', 'POST'])
@super_admin_required
def super_edit_institution(inst_id):
    institution = Institution.query.get_or_404(inst_id)
    if request.method == 'POST':
        institution.plan = request.form.get('plan')
        institution.session_limit = int(request.form.get('session_limit'))
        institution.sessions_used_this_month = int(request.form.get('sessions_used'))
        institution.billing_email = request.form.get('billing_email')
        institution.is_active = 'is_active' in request.form
        db.session.commit()
        return render_template('super_edit_institution.html', institution=institution, success='Institution updated successfully')
    return render_template('super_edit_institution.html', institution=institution)

@app.route('/super/billing')
@super_admin_required
def super_billing():
    institutions = Institution.query.all()
    total_revenue = sum({
        'free': 0, 'basic': 29, 'pro': 99, 'enterprise': 499
    }.get(i.plan, 0) for i in institutions if i.is_active)
    return render_template('super_billing.html', institutions=institutions, total_revenue=total_revenue)

@app.route('/super/analytics')
@super_admin_required
def super_analytics():
    from sqlalchemy import func
    sessions_by_month = db.session.query(
        func.strftime('%Y-%m', ExamSession.start_time).label('month'),
        func.count(ExamSession.id).label('count')
    ).filter(ExamSession.start_time.isnot(None)).group_by('month').order_by('month').all()
    return render_template('super_analytics.html', sessions_by_month=sessions_by_month)

@app.route('/super/logs')
@super_admin_required
def super_logs():
    import os
    log_file = 'logs/ai_invigilator.log'
    logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = f.readlines()[-100:][::-1]
    return render_template('super_logs.html', logs=logs)

@app.route('/super/settings', methods=['GET', 'POST'])
@super_admin_required
def super_settings():
    if request.method == 'POST':
        # Save global settings to database or config file
        return render_template('super_settings.html', success='Settings saved')
    return render_template('super_settings.html')


# ════════════════════════════════════════════════════
# SPECIALIST QUESTION ROUTES
# ════════════════════════════════════════════════════

@app.route('/run_code', methods=['POST'])
def run_code():
    """Execute code via Judge0 API (invigilator only during review)"""
    import requests
    
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'code_python')
    session_id = data.get('session_id')
    role = data.get('role', 'student')
    
    # Students cannot run code - only invigilators can during review
    if role != 'invigilator':
        return jsonify({
            'success': False,
            'error': 'Code execution is only available to invigilators during review'
        }), 403
    
    # Judge0 language IDs
    JUDGE0_LANG = {
        'code_python': 71,    # Python 3.8.1
        'code_javascript': 63, # JavaScript (Node.js 12.14.0)
        'code_java': 62,      # Java 8
        'code_cpp': 54,       # C++ (GCC 7.4.0)
        'code_sql': 82,       # SQL (SQLite 3.27.2)
    }
    
    judge0_lang_id = JUDGE0_LANG.get(language, 71)
    
    # Check for Judge0 API key
    api_key = os.environ.get('JUDGE0_API_KEY')
    
    if not api_key:
        # No API key - return mock response for development
        return jsonify({
            'success': True,
            'stdout': f'[Development mode] Code would run with Judge0.\nLanguage: {language}\nCode length: {len(code)} chars',
            'stderr': '',
            'time': '0.01',
            'memory': 1024
        })
    
    try:
        # Submit to Judge0
        submit_url = 'https://judge0-ce.p.rapidapi.com/submissions'
        headers = {
            'content-type': 'application/json',
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': 'judge0-ce.p.rapidapi.com'
        }
        
        payload = {
            'source_code': code,
            'language_id': judge0_lang_id,
            'stdin': '',
            'expected_output': None
        }
        
        response = requests.post(submit_url, json=payload, headers=headers)
        submission = response.json()
        
        # Get result
        token = submission.get('token')
        if not token:
            return jsonify({
                'success': False,
                'error': 'Failed to submit code to Judge0'
            }), 500
        
        # Poll for result
        result_url = f'https://judge0-ce.p.rapidapi.com/submissions/{token}'
        max_attempts = 30
        for _ in range(max_attempts):
            result_response = requests.get(result_url, headers=headers)
            result = result_response.json()
            
            if result.get('status', {}).get('id') > 2:  # Processing
                break
            time.sleep(0.5)
        
        # Extract output
        stdout = result.get('stdout', '') or ''
        stderr = result.get('stderr', '') or ''
        compile_error = result.get('compile_output', '') or ''
        status = result.get('status', {}).get('description', 'Unknown')
        exec_time = result.get('time', '0')
        memory = result.get('memory', 0)
        
        # Check for errors
        if compile_error:
            return jsonify({
                'success': False,
                'error': f'Compilation Error: {compile_error}',
                'time': exec_time,
                'memory': memory
            })
        
        if stderr:
            return jsonify({
                'success': True,
                'stdout': stdout,
                'stderr': stderr,
                'time': exec_time,
                'memory': memory
            })
        
        return jsonify({
            'success': True,
            'stdout': stdout or '(no output)',
            'stderr': '',
            'time': exec_time,
            'memory': memory
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Network error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Execution error: {str(e)}'
        }), 500


@app.route('/grade_answer', methods=['POST'])
@login_required('invigilator')
def grade_answer():
    """Allow invigilators to grade answers (especially code questions)"""
    data = request.json
    answer_id = data.get('answer_id')
    points = int(data.get('points_earned', 0))
    feedback = data.get('feedback', '')
    
    answer = Answer.query.get(answer_id)
    if not answer:
        return jsonify({'success': False, 'message': 'Answer not found'})
    
    # Security: invigilator can only grade answers in their institution
    inst_id = get_current_institution_id()
    if inst_id:
        session = ExamSession.query.get(answer.session_id)
        if session and session.institution_id != inst_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Cap points at question max
    if answer.question:
        points = min(points, answer.question.points)
    
    answer.points_earned = points
    answer.grading_feedback = feedback
    answer.graded_by = flask_session.get('user_id')
    answer.graded_at = datetime.utcnow()
    
    # Recalculate session total score
    session = ExamSession.query.get(answer.session_id)
    if session:
        all_answers = Answer.query.filter_by(session_id=session.id).all()
        session.total_score = sum(a.points_earned or 0 for a in all_answers)
        if session.max_score:
            session.percentage = (session.total_score / session.max_score * 100) if session.max_score > 0 else 0
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'points_earned': points,
        'total_score': session.total_score if session else None
    })


@app.route('/debug_login')
def debug_login():
    """Debug route to check login status"""
    from flask import session
    return jsonify({
        'session': dict(session),
        'logged_in': 'user_id' in session,
        'role': session.get('role'),
        'user_id': session.get('user_id'),
        'name': session.get('name'),
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', threaded=True)
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session as flask_session
import cv2
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd
from io import BytesIO

LOCAL_TZ = pytz.timezone('Africa/Nairobi')

def get_local_time():
    return datetime.now(LOCAL_TZ)

from config import Config, get_config
from database import db, ExamSession, Invigilator, Student, Alert, Question, Answer
from face_detection import FaceDetector
from eye_tracking import EyeTracker
from audio_monitor import AudioMonitor
from screen_monitor import ScreenMonitor
from alert_system import AlertSystem
from report_generator import ReportGenerator
from student_registration import StudentRegistration
from email_service import mail, EmailService
from sms_service import SMSService
from auto_grader import AutoGrader
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
    return response

app.config.from_object(get_config())

db.init_app(app)
migrate = Migrate(app, db)
mail.init_app(app)
app.register_blueprint(api)

Config.init_app(app)

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
@app.template_filter('from_json')
def from_json_filter(s):
    return json.loads(s) if s else {}

face_detector = FaceDetector()
eye_tracker = EyeTracker()
audio_monitor = AudioMonitor()
screen_monitor = ScreenMonitor()
alert_system = AlertSystem()
report_generator = ReportGenerator()
student_registration = StudentRegistration()
sms_service = SMSService()
auto_grader = AutoGrader()

active_cameras = {}
camera_locks = {}

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/<role>', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def login(role):
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if role == 'invigilator':
            user = Invigilator.query.filter_by(email=email).first()
            if user and user.check_password(password):
                SessionManager.create_session(str(user.id), user.id)
                flask_session['user_id'] = user.id
                flask_session['role'] = role
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

@app.route('/invigilator/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def invigilator_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if Invigilator.query.filter_by(email=email).first():
            return render_template('invigilator_register.html', error='Email already exists')
        invigilator = Invigilator(name=name, email=email)
        invigilator.set_password(password)
        db.session.add(invigilator)
        db.session.commit()
        return redirect(url_for('login', role='invigilator'))
    return render_template('invigilator_register.html')

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
    past_exams = ExamSession.query.filter_by(student_id=student.id).filter(
        ExamSession.status.in_(['completed', 'failed'])).order_by(ExamSession.start_time.desc()).all()
    scheduled_exams = ExamSession.query.filter_by(student_id=student.id, status='scheduled').order_by(
        ExamSession.scheduled_start).all()
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

    existing_session = ExamSession.query.filter_by(
        student_id=student.id, exam_name=exam_name, status='completed').first()
    if existing_session:
        return jsonify({'success': False, 'message': 'You have already completed this exam.'})

    active_session = ExamSession.query.filter_by(
        student_id=student.id, exam_name=exam_name, status='in_progress').first()
    if active_session:
        return jsonify({'success': False, 'message': 'You already have an active session for this exam.'})

    session = ExamSession(
        student_id=student.id,
        exam_name=exam_name,
        status='in_progress',
        start_time=datetime.utcnow()
    )
    db.session.add(session)
    db.session.commit()

    camera = None
    for i in range(5):
        try:
            temp_camera = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if temp_camera.isOpened():
                ret, test_frame = temp_camera.read()
                if ret and test_frame is not None:
                    camera = temp_camera
                    break
                else:
                    temp_camera.release()
            else:
                temp_camera.release()
        except:
            pass

    if not camera:
        session.status = 'failed'
        db.session.commit()
        return jsonify({'success': False, 'message': 'Camera not available'})

    active_cameras[session.id] = camera
    camera_locks[session.id] = threading.Lock()

    # Bind this exam session to the student's device for tamper detection
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

    if session_id in active_cameras:
        with camera_locks.get(session_id, threading.Lock()):
            active_cameras[session_id].release()
            del active_cameras[session_id]
            del camera_locks[session_id]

    audio_monitor.stop_session(session_id)
    screen_monitor.stop_session(session_id)
    alert_system.clear_session(session_id)

    return jsonify({'success': True, 'session_id': session_id})

def generate_frames(session_id):
    camera = active_cameras.get(session_id)
    lock = camera_locks.get(session_id)
    if not camera or not lock:
        return
    while session_id in active_cameras:
        with lock:
            if session_id not in active_cameras:
                break
            success, frame = camera.read()
            if not success:
                break
        face_count, detections = face_detector.detect_faces(frame)
        if face_count != 1:
            alert_system.check_face_violations(face_count, session_id)
        try:
            hand_results = face_detector.detect_hands(frame)
            alert_system.check_phone_usage(hand_results['phone_detected'], session_id)
            alert_system.check_help_request(hand_results['raised_hand_detected'], session_id)
        except Exception as e:
            print(f"Hand detection error: {e}")
        face_landmarks = face_detector.get_face_landmarks(frame)
        if face_landmarks is not None:
            is_looking, _ = eye_tracker.is_looking_at_screen(face_landmarks, frame.shape)
            if not is_looking:
                alert_system.check_gaze_violation(False, session_id)
        frame = face_detector.draw_detections(frame, detections)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.1)

@app.route('/video_feed/<int:session_id>')
def video_feed(session_id):
    if session_id not in active_cameras:
        return "No active session", 404
    return Response(generate_frames(session_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/tab_switch', methods=['POST'])
def tab_switch():
    session_id = request.json.get('session_id') if request.json else None
    if session_id:
        tab_switches = Alert.query.filter_by(session_id=session_id, alert_type='tab_switch').count()
        if tab_switches >= app.config['TAB_SWITCH_THRESHOLD']:
            screen_monitor.tab_switch(session_id)
            alert_system.check_tab_switch(session_id)
        elif tab_switches == app.config['TAB_SWITCH_THRESHOLD'] - 1:
            alert = Alert(
                session_id=session_id,
                alert_type='tab_switch',
                severity='medium',
                description=f'Tab switched {tab_switches + 1} times (threshold: {app.config["TAB_SWITCH_THRESHOLD"]})'
            )
            db.session.add(alert)
            db.session.commit()
    return jsonify({'success': True})

@app.route('/window_event', methods=['POST'])
def window_event():
    data = request.json or {}
    session_id = data.get('session_id')
    event_type = data.get('event_type')
    if session_id:
        if event_type == 'blur':
            screen_monitor.window_blur(session_id)
        elif event_type == 'focus':
            screen_monitor.window_focus(session_id)
    return jsonify({'success': True})

@app.route('/proctoring_alert', methods=['POST'])
@block_automation
def proctoring_alert():
    data = request.json
    session_id = data.get('session_id')
    alert_type = data.get('alert_type')
    description = data.get('description')
    if session_id:
        severity_map = {
            'multiple_faces': 'critical',
            'no_face_detected': 'high',
            'fullscreen_exit': 'high',
            'devtools_detected': 'high',
            'copy_attempt': 'medium',
            'screenshot_attempt': 'medium',
            'screen_sharing': 'critical',
            'multiple_monitors': 'medium',
            'view_source_attempt': 'medium',
        }
        severity = severity_map.get(alert_type, 'medium')
        alert = Alert(
            session_id=session_id,
            alert_type=alert_type,
            severity=severity,
            description=description
        )
        db.session.add(alert)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/request_help', methods=['POST'])
def request_help():
    session_id = request.json.get('session_id')
    if session_id:
        alert = Alert(
            session_id=session_id,
            alert_type='help_requested',
            severity='high',
            description='Student requested immediate assistance'
        )
        db.session.add(alert)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/camera_issue', methods=['POST'])
def camera_issue():
    data = request.json
    student_id = data.get('student_id')
    student_name = data.get('student_name')
    issue = data.get('issue')
    student = Student.query.filter_by(student_id=student_id).first()
    if student:
        alert = Alert(
            session_id=None,
            alert_type='camera_issue',
            severity='critical',
            description=f'{student_name} (ID: {student_id}) - Camera Issue: {issue}'
        )
        db.session.add(alert)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/upload_snapshot', methods=['POST'])
def upload_snapshot():
    import base64
    data = request.json
    session_id = data.get('session_id')
    snapshot = data.get('snapshot')
    if session_id and snapshot:
        snapshot_dir = os.path.join('static', 'snapshots')
        os.makedirs(snapshot_dir, exist_ok=True)
        image_data = snapshot.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        filename = f'session_{session_id}_latest.jpg'
        with open(os.path.join(snapshot_dir, filename), 'wb') as f:
            f.write(image_bytes)
    return jsonify({'success': True})

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
    all_scheduled = ExamSession.query.filter_by(status='scheduled').order_by(ExamSession.scheduled_start).all()
    from collections import defaultdict
    exams_grouped = defaultdict(list)
    for exam in all_scheduled:
        exams_grouped[exam.exam_name].append(exam)
    return render_template('exam_schedule.html', exams_grouped=exams_grouped, flask_session=flask_session)

@app.route('/bulk_import', methods=['GET', 'POST'])
@login_required('invigilator')
def bulk_import():
    if request.method == 'POST':
        try:
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
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return render_template('bulk_import.html', error=f'Missing columns: {", ".join(missing_cols)}', flask_session=flask_session)
            imported = 0
            skipped = 0
            skipped_list = []
            credentials = []
            rows = list(df.iterrows())
            for idx, row in rows:
                try:
                    existing = Student.query.filter_by(student_id=row['student_id']).first()
                    if existing:
                        skipped += 1
                        skipped_list.append(f"{row['name']} ({row['student_id']}) - Already exists")
                        continue
                    password = str(row['student_id'])
                    student = Student(
                        name=row['name'], student_id=row['student_id'],
                        email=row['email'], cohort=row.get('cohort', 'Default'))
                    student.set_password(password)
                    student.email_verified = True
                    db.session.add(student)
                    credentials.append({'name': row['name'], 'student_id': row['student_id'], 'email': row['email'], 'password': password})
                    imported += 1
                except Exception as e:
                    db.session.rollback()
                    skipped += 1
                    skipped_list.append(f"{row.get('name', 'Unknown')} - Error: {str(e)}")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    db.session.commit()
                    break
                except Exception as commit_error:
                    if "database is locked" in str(commit_error).lower():
                        db.session.rollback()
                        time.sleep(0.5 * (attempt + 1))
                    else:
                        db.session.rollback()
                        raise
            message = f'{imported} students imported, {skipped} skipped'
            if skipped > 0 and imported == 0:
                message = f'All {skipped} students already exist. Delete existing students first or use different IDs.'
            if notify_email and imported > 0:
                try:
                    email_service = EmailService()
                    body = f'<h2>Import Summary</h2><p>Imported: {imported}, Skipped: {skipped}</p>'
                    email_service.send_email(notify_email, f'Bulk Import - {imported} Students Added', body)
                except Exception as e:
                    print(f"Email notification failed: {e}")
            return render_template('bulk_import.html',
                                 success=message if imported > 0 else None,
                                 error=message if imported == 0 else None,
                                 credentials=credentials,
                                 skipped_list=skipped_list[:20],
                                 email_sent=notify_email if (notify_email and imported > 0) else None,
                                 flask_session=flask_session)
        except Exception as e:
            return render_template('bulk_import.html', error=f'Import failed: {str(e)}', flask_session=flask_session)
    return render_template('bulk_import.html', flask_session=flask_session)

@app.route('/manage_questions/<exam_name>', methods=['GET', 'POST'])
@login_required('invigilator')
def manage_questions(exam_name):
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        question_type = request.form.get('question_type')
        points = int(request.form.get('points', 1))
        question = Question(
            exam_name=exam_name, question_text=question_text,
            question_type=question_type, points=points,
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
    if student_id:
        session = ExamSession(student_id=student_id, exam_name=exam_name,
                              scheduled_start=scheduled_start, duration_minutes=duration_minutes, status='scheduled')
        db.session.add(session)
    else:
        students = Student.query.filter_by(cohort=cohort).all()
        if not students:
            return f"No students found in cohort '{cohort}'", 400
        for student in students:
            session = ExamSession(student_id=student.id, exam_name=exam_name,
                                  scheduled_start=scheduled_start, duration_minutes=duration_minutes, status='scheduled')
            db.session.add(session)
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
    return render_template('error.html', code=404, message='Page not found'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500, message='Server error'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, message='Access denied'), 403

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', threaded=True)
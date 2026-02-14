from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session as flask_session
import cv2
import time
from datetime import datetime, timedelta
import pytz

# Set timezone
LOCAL_TZ = pytz.timezone('Africa/Nairobi')  # Kenya timezone

def get_local_time():
    return datetime.now(LOCAL_TZ)
from config import Config
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
from functools import wraps
import threading
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail.init_app(app)
app.register_blueprint(api)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Add JSON filter for templates
import json
@app.template_filter('from_json')
def from_json_filter(s):
    return json.loads(s) if s else {}

# Initialize monitoring components
face_detector = FaceDetector()
eye_tracker = EyeTracker()
audio_monitor = AudioMonitor()
screen_monitor = ScreenMonitor()
alert_system = AlertSystem()
report_generator = ReportGenerator()
student_registration = StudentRegistration()
sms_service = SMSService()
auto_grader = AutoGrader()

# Per-session cameras (thread-safe)
active_cameras = {}
camera_locks = {}

def login_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in flask_session or flask_session.get('role') != role:
                return redirect(url_for('login', role=role))
            # Session timeout check
            last_activity = flask_session.get('last_activity')
            if last_activity:
                if datetime.now() - datetime.fromisoformat(last_activity) > timedelta(hours=1):
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
        else:
            user = Student.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            flask_session['user_id'] = user.id
            flask_session['role'] = role
            flask_session['name'] = user.name
            
            if role == 'invigilator':
                return redirect(url_for('invigilator_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            error_msg = 'Invalid credentials'
            if role == 'student' and user and not user.password_hash:
                error_msg = 'Student account needs to be re-registered with password'
            return render_template('login.html', role=role, error=error_msg)
    
    return render_template('login.html', role=role)

@app.route('/logout')
def logout():
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
    recent_alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(20).all()
    all_students = Student.query.all()
    # Get unique cohorts
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
    
    # Check for active in-progress exam
    active_exam = ExamSession.query.filter_by(student_id=student.id, status='in_progress').first()
    
    # Check if active exam has expired
    expired_message = None
    if active_exam and active_exam.scheduled_start and active_exam.duration_minutes:
        exam_end_time = active_exam.start_time + timedelta(minutes=active_exam.duration_minutes)
        if datetime.utcnow() > exam_end_time:
            # Mark as failed due to timeout
            active_exam.status = 'failed'
            active_exam.end_time = exam_end_time
            db.session.commit()
            expired_message = f'Your exam "{active_exam.exam_name}" has expired. Please contact your invigilator.'
            active_exam = None
    
    past_exams = ExamSession.query.filter_by(student_id=student.id).filter(ExamSession.status.in_(['completed', 'failed'])).order_by(ExamSession.start_time.desc()).all()
    scheduled_exams = ExamSession.query.filter_by(student_id=student.id, status='scheduled').order_by(ExamSession.scheduled_start).all()
    
    return render_template('student_dashboard.html', 
                         student=student, 
                         past_exams=past_exams, 
                         scheduled_exams=scheduled_exams,
                         active_exam=active_exam,
                         expired_message=expired_message,
                         now=datetime.now)

@app.route('/student/register', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def student_register():
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        photo = request.files.get('photo')
        
        if Student.query.filter_by(student_id=student_id).first():
            return render_template('student_register.html', error='Student ID already exists')
        
        if Student.query.filter_by(email=email).first():
            return render_template('student_register.html', error='Email already exists')
        
        student, message = student_registration.register_student(name, student_id, email, photo, password)
        if student:
            student.email_verified = True
            db.session.commit()
            return redirect(url_for('login', role='student'))
        return render_template('student_register.html', error=message)
    
    return render_template('student_register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # GET request - check login
    if request.method == 'GET':
        if 'user_id' not in flask_session or flask_session.get('role') != 'invigilator':
            return redirect(url_for('login', role='invigilator'))
        return render_template('register.html', flask_session=flask_session)
    
    # POST request
    if 'user_id' not in flask_session or flask_session.get('role') != 'invigilator':
        return jsonify({'success': False, 'message': 'Unauthorized - Invigilator login required'})
    
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
    # Group by cohort
    from collections import defaultdict
    cohorts = defaultdict(list)
    for student in all_students:
        cohorts[student.cohort or 'Uncategorized'].append(student)
    # Sort cohorts alphabetically
    sorted_cohorts = dict(sorted(cohorts.items()))
    return render_template('students.html', cohorts=sorted_cohorts)

@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required('invigilator')
def delete_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'})
    
    # Delete related sessions and alerts
    ExamSession.query.filter_by(student_id=student_id).delete()
    db.session.delete(student)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/delete_cohort', methods=['POST'])
@login_required('invigilator')
def delete_cohort():
    cohort = request.json.get('cohort')
    students = Student.query.filter_by(cohort=cohort).all()
    count = len(students)
    
    for student in students:
        ExamSession.query.filter_by(student_id=student.id).delete()
        db.session.delete(student)
    
    db.session.commit()
    return jsonify({'success': True, 'count': count})

@app.route('/delete_all_students', methods=['POST'])
@login_required('invigilator')
def delete_all_students():
    count = Student.query.count()
    ExamSession.query.delete()
    Alert.query.delete()
    Student.query.delete()
    db.session.commit()
    
    return jsonify({'success': True, 'count': count})

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
            # Load questions for this exam
            questions = Question.query.filter_by(exam_name=exam_session.exam_name).order_by(Question.order).all()
    
    return render_template('exam.html', student=student, exam_session=exam_session, is_resume=is_resume, questions=questions)

@app.route('/submit_answer', methods=['POST'])
@login_required('student')
def submit_answer():
    data = request.json
    session_id = data.get('session_id')
    question_id = data.get('question_id')
    answer_text = data.get('answer_text')
    
    # Check if answer already exists
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
def start_exam():
    data = request.json
    student_id = data.get('student_id')
    exam_name = data.get('exam_name')
    
    student = student_registration.get_student(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'})
    
    # Check if student already completed this exam
    existing_session = ExamSession.query.filter_by(
        student_id=student.id,
        exam_name=exam_name,
        status='completed'
    ).first()
    
    if existing_session:
        return jsonify({'success': False, 'message': 'You have already completed this exam. Contact your invigilator if you need to retake it.'})
    
    # Check if student has an active session for this exam
    active_session = ExamSession.query.filter_by(
        student_id=student.id,
        exam_name=exam_name,
        status='in_progress'
    ).first()
    
    if active_session:
        return jsonify({'success': False, 'message': 'You already have an active session for this exam. Please end it first.'})
    
    # Create exam session
    session = ExamSession(
        student_id=student.id,
        exam_name=exam_name,
        status='in_progress',
        start_time=datetime.utcnow()
    )
    db.session.add(session)
    db.session.commit()
    
    # Initialize camera for this session - try all indices
    camera = None
    for i in range(5):  # Try indices 0-4
        try:
            temp_camera = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if temp_camera.isOpened():
                ret, test_frame = temp_camera.read()
                if ret and test_frame is not None:
                    camera = temp_camera
                    print(f"Camera opened on index {i}")
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
    
    # Store camera per session
    active_cameras[session.id] = camera
    camera_locks[session.id] = threading.Lock()
    
    return jsonify({'success': True, 'session_id': session.id})

@app.route('/end_exam', methods=['POST'])
def end_exam():
    session_id = request.json.get('session_id') if request.json else None
    
    if not session_id:
        return jsonify({'success': False, 'message': 'No session ID'})
    
    session = ExamSession.query.get(session_id)
    if session:
        session.end_time = datetime.utcnow()
        session.status = 'completed'
        db.session.commit()
        
        # Auto-grade the exam
        grading_result = auto_grader.grade_session(session_id)
        
        # Send SMS notification
        if session.student.phone_number:
            sms_service.send_exam_completed(
                session.student.phone_number,
                session.student.name,
                session.exam_name
            )
    
    # Release camera for this session
    if session_id in active_cameras:
        with camera_locks.get(session_id, threading.Lock()):
            active_cameras[session_id].release()
            del active_cameras[session_id]
            del camera_locks[session_id]
    
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
        
        # Face detection
        face_count, detections = face_detector.detect_faces(frame)
        
        # Check violations
        if face_count != 1:
            alert_system.check_face_violations(face_count, session_id)
        
        # Eye tracking
        face_landmarks = face_detector.get_face_landmarks(frame)
        if face_landmarks is not None:
            is_looking, _ = eye_tracker.is_looking_at_screen(face_landmarks, frame.shape)
            if not is_looking:
                alert_system.check_gaze_violation(False, session_id)
        
        # Draw detections
        frame = face_detector.draw_detections(frame, detections)
        
        # Encode
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        time.sleep(0.03)

@app.route('/video_feed/<int:session_id>')
def video_feed(session_id):
    if session_id not in active_cameras:
        return "No active session", 404
    return Response(generate_frames(session_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/tab_switch', methods=['POST'])
def tab_switch():
    session_id = request.json.get('session_id') if request.json else None
    if session_id:
        screen_monitor.detect_tab_switch()
        alert_system.check_tab_switch(session_id)
    return jsonify({'success': True})

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
    return Response(pdf_buffer.getvalue(), mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename=exam_report_{session_id}.pdf'})

@app.route('/sessions')
@login_required('invigilator')
def sessions():
    all_sessions = ExamSession.query.order_by(ExamSession.start_time.desc()).all()
    return render_template('sessions.html', sessions=all_sessions)

@app.route('/alerts')
@login_required('invigilator')
def alerts():
    all_alerts = Alert.query.order_by(Alert.timestamp.desc()).all()
    return render_template('alerts.html', alerts=all_alerts, flask_session=flask_session)

@app.route('/exam_schedule')
@login_required('invigilator')
def exam_schedule():
    all_scheduled = ExamSession.query.filter_by(status='scheduled').order_by(ExamSession.scheduled_start).all()
    
    # Group by exam name
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
            import pandas as pd
            
            file = request.files.get('csv_file')
            notify_email = request.form.get('notify_email')
            
            if not file:
                return render_template('bulk_import.html', error='No file uploaded', flask_session=flask_session)
            
            # Read CSV or Excel
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
            
            # Validate required columns
            required_cols = ['name', 'student_id', 'email']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return render_template('bulk_import.html', error=f'Missing required columns: {", ".join(missing_cols)}', flask_session=flask_session)
            
            imported = 0
            skipped = 0
            skipped_list = []
            credentials = []
            
            for _, row in df.iterrows():
                try:
                    existing = Student.query.filter_by(student_id=row['student_id']).first()
                    if existing:
                        skipped += 1
                        skipped_list.append(f"{row['name']} ({row['student_id']}) - Already exists")
                        continue
                    
                    # Use student_id as password
                    password = str(row['student_id'])
                    student = Student(
                        name=row['name'],
                        student_id=row['student_id'],
                        email=row['email'],
                        cohort=row.get('cohort', 'Default')
                    )
                    student.set_password(password)
                    student.email_verified = True
                    db.session.add(student)
                    credentials.append({'name': row['name'], 'student_id': row['student_id'], 'email': row['email'], 'password': password})
                    imported += 1
                except Exception as e:
                    print(f"Error importing row: {e}")
                    skipped += 1
                    skipped_list.append(f"{row.get('name', 'Unknown')} - Error: {str(e)}")
                    continue
            
            db.session.commit()
            
            message = f'{imported} students imported, {skipped} skipped'
            if skipped > 0 and imported == 0:
                message = f'All {skipped} students already exist in database. Delete existing students first or use different student IDs.'
            
            # Send notification email if provided
            if notify_email and imported > 0:
                try:
                    email_service = EmailService()
                    subject = f'Bulk Import Complete - {imported} Students Added'
                    body = f'''
                    <h2>Student Import Summary</h2>
                    <p><strong>Imported:</strong> {imported} students</p>
                    <p><strong>Skipped:</strong> {skipped} students</p>
                    <p><strong>File:</strong> {file.filename}</p>
                    <p><strong>Imported by:</strong> {flask_session.get('name')}</p>
                    <hr>
                    <h3>Student Credentials</h3>
                    <p>Students can login with their Student ID as password:</p>
                    <table border="1" cellpadding="8" style="border-collapse: collapse;">
                        <tr><th>Name</th><th>Student ID</th><th>Email</th></tr>
                        {''.join([f'<tr><td>{c["name"]}</td><td>{c["student_id"]}</td><td>{c["email"]}</td></tr>' for c in credentials[:50]])}
                    </table>
                    {f'<p><em>Showing first 50 of {len(credentials)} students</em></p>' if len(credentials) > 50 else ''}
                    '''
                    email_service.send_email(notify_email, subject, body)
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
    
    # Find student
    student = Student.query.filter_by(student_id=student_id).first()
    if student:
        # Create alert without session (pre-exam issue)
        alert = Alert(
            session_id=None,
            alert_type='camera_issue',
            severity='critical',
            description=f'{student_name} (ID: {student_id}) - Camera Issue: {issue}'
        )
        db.session.add(alert)
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/proctoring_alert', methods=['POST'])
def proctoring_alert():
    data = request.json
    session_id = data.get('session_id')
    alert_type = data.get('alert_type')
    description = data.get('description')
    
    if session_id:
        severity = 'high' if alert_type in ['multiple_faces', 'no_face_detected'] else 'medium'
        alert = Alert(
            session_id=session_id,
            alert_type=alert_type,
            severity=severity,
            description=description
        )
        db.session.add(alert)
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/upload_snapshot', methods=['POST'])
def upload_snapshot():
    import base64
    import os
    
    data = request.json
    session_id = data.get('session_id')
    snapshot = data.get('snapshot')
    
    if session_id and snapshot:
        # Create snapshots directory
        snapshot_dir = os.path.join('static', 'snapshots')
        os.makedirs(snapshot_dir, exist_ok=True)
        
        # Save snapshot
        image_data = snapshot.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        filename = f'session_{session_id}_latest.jpg'
        filepath = os.path.join(snapshot_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
    
    return jsonify({'success': True})

@app.route('/get_snapshot/<int:session_id>')
@login_required('invigilator')
def get_snapshot(session_id):
    import os
    from flask import send_file
    
    filepath = os.path.join('static', 'snapshots', f'session_{session_id}_latest.jpg')
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/jpeg')
    else:
        # Return placeholder
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
            alert_dict['session'] = {
                'student': {
                    'name': alert.session.student.name
                }
            }
        alerts_data.append(alert_dict)
    return jsonify({'alerts': alerts_data})

@app.route('/manage_questions/<exam_name>', methods=['GET', 'POST'])
@login_required('invigilator')
def manage_questions(exam_name):
    if request.method == 'POST':
        import json
        question_text = request.form.get('question_text')
        question_type = request.form.get('question_type')
        points = int(request.form.get('points', 1))
        
        question = Question(
            exam_name=exam_name,
            question_text=question_text,
            question_type=question_type,
            points=points,
            order=Question.query.filter_by(exam_name=exam_name).count() + 1
        )
        
        if question_type == 'multiple_choice':
            options = {
                'A': request.form.get('option_a'),
                'B': request.form.get('option_b'),
                'C': request.form.get('option_c'),
                'D': request.form.get('option_d')
            }
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
    
    # Get grading results
    results = auto_grader.get_session_results(session_id)
    
    questions = Question.query.filter_by(exam_name=session.exam_name).order_by(Question.order).all()
    answers = {a.question_id: a for a in Answer.query.filter_by(session_id=session_id).all()}
    
    return render_template('view_answers.html', 
                         session=session, 
                         questions=questions, 
                         answers=answers,
                         results=results,
                         flask_session=flask_session)

@app.route('/delete_exam/<int:exam_id>', methods=['POST'])
@login_required('invigilator')
def delete_exam(exam_id):
    exam = ExamSession.query.get(exam_id)
    if exam:
        # Delete related answers and alerts
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
    count = len(exams)
    
    for exam in exams:
        Answer.query.filter_by(session_id=exam.id).delete()
        Alert.query.filter_by(session_id=exam.id).delete()
        db.session.delete(exam)
    
    db.session.commit()
    return jsonify({'success': True, 'count': count})

@app.route('/schedule_exam', methods=['POST'])
@login_required('invigilator')
def schedule_exam():
    cohort = request.form.get('cohort')
    student_id = request.form.get('student_id')
    exam_name = request.form.get('exam_name')
    scheduled_start = datetime.fromisoformat(request.form.get('scheduled_start'))
    duration_minutes = int(request.form.get('duration_minutes'))
    
    if not cohort:
        return "Cohort is required", 400
    
    # Schedule for cohort or individual student
    if student_id:
        # Individual student
        session = ExamSession(
            student_id=student_id,
            exam_name=exam_name,
            scheduled_start=scheduled_start,
            duration_minutes=duration_minutes,
            status='scheduled'
        )
        db.session.add(session)
    else:
        # Entire cohort
        students = Student.query.filter_by(cohort=cohort).all()
        if not students:
            return f"No students found in cohort '{cohort}'", 400
        
        for student in students:
            session = ExamSession(
                student_id=student.id,
                exam_name=exam_name,
                scheduled_start=scheduled_start,
                duration_minutes=duration_minutes,
                status='scheduled'
            )
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
    alert = Alert(
        session_id=session_id,
        alert_type='manual_flag',
        severity='high',
        description='Session flagged by invigilator for review'
    )
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
    app.run(debug=True, host='0.0.0.0', threaded=True)

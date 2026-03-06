from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Institution(db.Model):
    __tablename__ = 'institutions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    plan = db.Column(db.String(50), default='free')  # free, basic, pro, enterprise
    session_limit = db.Column(db.Integer, default=100)  # Monthly session limit
    sessions_used_this_month = db.Column(db.Integer, default=0)
    billing_email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admins = db.relationship('Admin', backref='institution', lazy=True)
    students = db.relationship('Student', backref='institution', lazy=True)
    exam_sessions = db.relationship('ExamSession', backref='institution', lazy=True)

    @property
    def is_over_limit(self):
        return self.sessions_used_this_month >= self.session_limit

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    institution_name = db.Column(db.String(200), nullable=False)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    invigilators = db.relationship('Invigilator', backref='admin', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Invigilator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True)
    assigned_cohorts = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def cohort_list(self):
        if not self.assigned_cohorts:
            return []
        return [c.strip() for c in self.assigned_cohorts.split(',')]

    @cohort_list.setter
    def cohort_list(self, cohorts):
        self.assigned_cohorts = ','.join(cohorts)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))  # For SMS notifications
    password_hash = db.Column(db.String(200), nullable=False)
    photo_path = db.Column(db.String(200))
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    reset_token = db.Column(db.String(100), nullable=True)  # For password reset
    reset_token_expiry = db.Column(db.DateTime, nullable=True)  # Token expiration time
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True)
    # PERF: index=True speeds up cohort filtering queries
    cohort = db.Column(db.String(50), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    exam_sessions = db.relationship('ExamSession', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ExamSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # PERF: index=True speeds up per-student session queries
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=True)
    exam_name = db.Column(db.String(100), nullable=False)
    scheduled_start = db.Column(db.DateTime)
    scheduled_end = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    # PERF: index=True speeds up status filter queries (in_progress, completed, scheduled)
    status = db.Column(db.String(20), default='scheduled', index=True)
    recording_path = db.Column(db.String(200))
    total_score = db.Column(db.Integer, default=0)  # Auto-calculated score
    max_score = db.Column(db.Integer, default=0)  # Total possible points
    is_auto_submitted = db.Column(db.Boolean, default=False)  # True if auto-submitted due to time expiry
    alerts = db.relationship('Alert', backref='session', lazy=True)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # PERF: index=True speeds up per-session alert lookups
    session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'), nullable=True, index=True)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    # PERF: index=True speeds up ORDER BY timestamp queries on the dashboard
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    screenshot_path = db.Column(db.String(200))
    notified = db.Column(db.Boolean, default=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # PERF: index=True speeds up per-exam question loading
    exam_name = db.Column(db.String(100), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'multiple_choice', 'essay', 'code'
    options = db.Column(db.Text)  # JSON string for multiple choice options
    correct_answer = db.Column(db.String(10))  # For multiple choice (A, B, C, D)
    points = db.Column(db.Integer, default=1)
    order = db.Column(db.Integer)
    programming_language = db.Column(db.String(50))  # python, java, cpp, javascript, etc.
    allow_calculator = db.Column(db.Boolean, default=False)
    reference_image = db.Column(db.Text)  # Base64 image for graph questions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # PERF: index=True speeds up per-session answer retrieval
    session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_text = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)  # Auto-graded for MCQ
    points_earned = db.Column(db.Integer, default=0)  # Points for this answer
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    graded_by = db.Column(db.Integer, db.ForeignKey('invigilator.id'), nullable=True)
    grading_feedback = db.Column(db.Text, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    question = db.relationship('Question', backref='answers')

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'student_import', 'exam_scheduled', 'exam_started', 'critical_alert'
    description = db.Column(db.Text, nullable=False)
    invigilator_id = db.Column(db.Integer, db.ForeignKey('invigilator.id'), nullable=True)
    extra_data = db.Column(db.Text, nullable=True)  # JSON for extra data
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    invigilator = db.relationship('Invigilator', backref='activities')

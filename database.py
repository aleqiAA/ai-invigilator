from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Invigilator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    cohort = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    exam_sessions = db.relationship('ExamSession', backref='student', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ExamSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    exam_name = db.Column(db.String(100), nullable=False)
    scheduled_start = db.Column(db.DateTime)
    scheduled_end = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='scheduled')
    recording_path = db.Column(db.String(200))
    total_score = db.Column(db.Integer, default=0)  # Auto-calculated score
    max_score = db.Column(db.Integer, default=0)  # Total possible points
    is_auto_submitted = db.Column(db.Boolean, default=False)  # True if auto-submitted due to time expiry
    alerts = db.relationship('Alert', backref='session', lazy=True)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'), nullable=True)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    screenshot_path = db.Column(db.String(200))
    notified = db.Column(db.Boolean, default=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_name = db.Column(db.String(100), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # 'multiple_choice' or 'essay'
    options = db.Column(db.Text)  # JSON string for multiple choice options
    correct_answer = db.Column(db.String(10))  # For multiple choice (A, B, C, D)
    points = db.Column(db.Integer, default=1)
    order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_text = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)  # Auto-graded for MCQ
    points_earned = db.Column(db.Integer, default=0)  # Points for this answer
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    graded_by = db.Column(db.Integer, db.ForeignKey('invigilator.id'), nullable=True)
    grading_feedback = db.Column(db.Text, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    question = db.relationship('Question', backref='answers')

"""
Run this AFTER setting up PostgreSQL to migrate all your existing
SQLite data into PostgreSQL.

Steps:
1. pip install psycopg2-binary
2. Create the PostgreSQL database
3. Update your .env file
4. Run: python migrate_to_postgres.py
"""

import sqlite3
import os
from app import app, db
from database import Admin, Invigilator, Student, ExamSession, Alert, Question, Answer, ActivityLog

def find_sqlite_db():
    """Find the SQLite database file."""
    candidates = ['instance/ai_invigilator.db', 'instance/invigilator.db', 'instance/exam.db', 
                  'ai_invigilator.db', 'exam.db', 'database.db', 'site.db']
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def migrate():
    sqlite_path = find_sqlite_db()
    
    if not sqlite_path:
        print("No SQLite database found. Starting fresh PostgreSQL database.")
        with app.app_context():
            db.create_all()
            print("All tables created in PostgreSQL.")
        return

    print(f"Found SQLite database at: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    with app.app_context():
        db.create_all()
        print("Tables created in PostgreSQL")

        # Migrate Admins
        try:
            cursor.execute("SELECT * FROM admins")
            rows = cursor.fetchall()
            for row in rows:
                if not Admin.query.filter_by(email=row['email']).first():
                    admin = Admin(id=row['id'], name=row['name'], email=row['email'],
                                password_hash=row['password_hash'], institution_name=row['institution_name'],
                                is_active=row.get('is_active', True))
                    db.session.add(admin)
            db.session.commit()
            print(f"Migrated {len(rows)} admins")
        except Exception as e:
            db.session.rollback()
            print(f"  Admins: {e}")

        # Migrate Invigilators
        try:
            cursor.execute("SELECT * FROM invigilator")
            rows = cursor.fetchall()
            for row in rows:
                if not Invigilator.query.filter_by(email=row['email']).first():
                    inv = Invigilator(id=row['id'], name=row['name'], email=row['email'],
                                    password_hash=row['password_hash'], is_active=row.get('is_active', True),
                                    assigned_cohorts=row.get('assigned_cohorts'), admin_id=row.get('admin_id'))
                    db.session.add(inv)
            db.session.commit()
            print(f"Migrated {len(rows)} invigilators")
        except Exception as e:
            db.session.rollback()
            print(f"  Invigilators: {e}")

        # Migrate Students
        try:
            cursor.execute("SELECT * FROM student")
            rows = cursor.fetchall()
            for row in rows:
                if not Student.query.filter_by(student_id=row['student_id']).first():
                    s = Student(id=row['id'], name=row['name'], student_id=row['student_id'],
                              email=row['email'], password_hash=row['password_hash'],
                              cohort=row.get('cohort'), photo_path=row.get('photo_path'),
                              email_verified=row.get('email_verified', True))
                    db.session.add(s)
            db.session.commit()
            print(f"Migrated {len(rows)} students")
        except Exception as e:
            db.session.rollback()
            print(f"  Students: {e}")

        # Migrate ExamSessions
        try:
            cursor.execute("SELECT * FROM exam_session")
            rows = cursor.fetchall()
            for row in rows:
                if not ExamSession.query.get(row['id']):
                    es = ExamSession(id=row['id'], student_id=row['student_id'], exam_name=row['exam_name'],
                                   status=row['status'], scheduled_start=row.get('scheduled_start'),
                                   duration_minutes=row.get('duration_minutes'), start_time=row.get('start_time'),
                                   end_time=row.get('end_time'), total_score=row.get('total_score', 0),
                                   max_score=row.get('max_score', 0))
                    db.session.add(es)
            db.session.commit()
            print(f"Migrated {len(rows)} exam sessions")
        except Exception as e:
            db.session.rollback()
            print(f"  ExamSessions: {e}")

        # Migrate Alerts
        try:
            cursor.execute("SELECT * FROM alert")
            rows = cursor.fetchall()
            for row in rows:
                if not Alert.query.get(row['id']):
                    a = Alert(id=row['id'], session_id=row['session_id'], alert_type=row['alert_type'],
                            severity=row['severity'], description=row.get('description', ''))
                    db.session.add(a)
            db.session.commit()
            print(f"Migrated {len(rows)} alerts")
        except Exception as e:
            db.session.rollback()
            print(f"  Alerts: {e}")

        # Migrate Questions
        try:
            cursor.execute("SELECT * FROM question")
            rows = cursor.fetchall()
            for row in rows:
                if not Question.query.get(row['id']):
                    q = Question(id=row['id'], exam_name=row['exam_name'], question_text=row['question_text'],
                               question_type=row['question_type'], options=row.get('options'),
                               correct_answer=row.get('correct_answer'), points=row.get('points', 1),
                               order=row.get('order', 0), programming_language=row.get('programming_language'),
                               allow_calculator=row.get('allow_calculator', False))
                    db.session.add(q)
            db.session.commit()
            print(f"Migrated {len(rows)} questions")
        except Exception as e:
            db.session.rollback()
            print(f"  Questions: {e}")

        # Migrate Answers
        try:
            cursor.execute("SELECT * FROM answer")
            rows = cursor.fetchall()
            for row in rows:
                if not Answer.query.get(row['id']):
                    ans = Answer(id=row['id'], session_id=row['session_id'], question_id=row['question_id'],
                               answer_text=row.get('answer_text'), is_correct=row.get('is_correct'),
                               points_earned=row.get('points_earned', 0), graded_by=row.get('graded_by'),
                               grading_feedback=row.get('grading_feedback'), graded_at=row.get('graded_at'))
                    db.session.add(ans)
            db.session.commit()
            print(f"Migrated {len(rows)} answers")
        except Exception as e:
            db.session.rollback()
            print(f"  Answers: {e}")

        # Migrate ActivityLog
        try:
            cursor.execute("SELECT * FROM activity_logs")
            rows = cursor.fetchall()
            for row in rows:
                if not ActivityLog.query.get(row['id']):
                    log = ActivityLog(id=row['id'], admin_id=row['admin_id'], activity_type=row['activity_type'],
                                    description=row['description'], invigilator_id=row.get('invigilator_id'),
                                    extra_data=row.get('extra_data'))
                    db.session.add(log)
            db.session.commit()
            print(f"Migrated {len(rows)} activity logs")
        except Exception as e:
            db.session.rollback()
            print(f"  ActivityLog: {e}")

    sqlite_conn.close()
    print("\nMigration complete! Your data is now in PostgreSQL.")
    print("   You can now delete your .db file if everything looks correct.")

if __name__ == '__main__':
    migrate()

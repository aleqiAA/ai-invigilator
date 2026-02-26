import os
from werkzeug.utils import secure_filename
from database import db, Student
from config import Config
from sqlalchemy.exc import OperationalError
import time

class StudentRegistration:
    def __init__(self):
        self.allowed_extensions = {'png', 'jpg', 'jpeg'}

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def register_student(self, name, student_id, email, photo_file=None, password=None):
        # Check if student already exists
        existing = Student.query.filter_by(student_id=student_id).first()
        if existing:
            return None, "Student ID already exists"

        existing_email = Student.query.filter_by(email=email).first()
        if existing_email:
            return None, "Email already exists"

        # Save photo if provided
        photo_path = None
        if photo_file and self.allowed_file(photo_file.filename):
            filename = secure_filename(f"{student_id}_{photo_file.filename}")
            photo_path = os.path.join(Config.STUDENT_PHOTOS_PATH, filename)
            photo_file.save(photo_path)

        # Create student record
        student = Student(
            name=name,
            student_id=student_id,
            email=email,
            photo_path=photo_path
        )

        # Set password if provided
        if password:
            student.set_password(password)

        # Add to database with retry logic for locking issues
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                db.session.add(student)
                db.session.commit()
                return student, "Student registered successfully"
                
            except OperationalError as e:
                if "database is locked" in str(e).lower():
                    retry_count += 1
                    db.session.rollback()
                    time.sleep(0.5 * retry_count)  # Exponential backoff
                    continue
                else:
                    db.session.rollback()
                    raise e
            except Exception as e:
                db.session.rollback()
                raise e
        
        return None, f"Failed to register student after {max_retries} attempts due to database lock"
    
    def get_student(self, student_id):
        return Student.query.filter_by(student_id=student_id).first()
    
    def get_all_students(self):
        return Student.query.all()
    
    def update_student(self, student_id, name=None, email=None, photo_file=None):
        student = self.get_student(student_id)
        if not student:
            return None, "Student not found"
        
        if name:
            student.name = name
        if email:
            student.email = email
        if photo_file and self.allowed_file(photo_file.filename):
            filename = secure_filename(f"{student_id}_{photo_file.filename}")
            photo_path = os.path.join(Config.STUDENT_PHOTOS_PATH, filename)
            photo_file.save(photo_path)
            student.photo_path = photo_path
        
        db.session.commit()
        return student, "Student updated successfully"
    
    def delete_student(self, student_id):
        student = self.get_student(student_id)
        if not student:
            return False, "Student not found"
        
        db.session.delete(student)
        db.session.commit()
        return True, "Student deleted successfully"

    def delete_all_students(self):
        """Delete all students and return the count of deleted records."""
        try:
            count = Student.query.count()
            Student.query.delete()
            db.session.commit()
            return True, count, "All students deleted successfully"
        except OperationalError as e:
            db.session.rollback()
            return False, 0, f"Database error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, 0, str(e)

    def delete_cohort(self, cohort_name):
        """Delete all students belonging to a specific cohort."""
        try:
            students = Student.query.filter_by(cohort=cohort_name).all()
            count = len(students)
            for student in students:
                db.session.delete(student)
            db.session.commit()
            return True, count, f"Cohort '{cohort_name}' deleted successfully"
        except OperationalError as e:
            db.session.rollback()
            return False, 0, f"Database error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, 0, str(e)
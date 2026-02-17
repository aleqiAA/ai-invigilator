from marshmallow import Schema, fields, validate, validates_schema, ValidationError
import re

class StudentRegistrationSchema(Schema):
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    phone = fields.Str(validate=validate.Length(min=10, max=15))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class ExamStartSchema(Schema):
    student_id = fields.Str(required=True)
    exam_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))

class AnswerSubmissionSchema(Schema):
    session_id = fields.Str(required=True)
    question_id = fields.Str(required=True)
    answer_text = fields.Str(required=True)

class AlertReportSchema(Schema):
    session_id = fields.Str(required=True)
    alert_type = fields.Str(required=True)
    description = fields.Str(required=True)

class GradeSubmissionSchema(Schema):
    session_id = fields.Str(required=True)
    score = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    feedback = fields.Str()

def validate_email_format(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    """Validate password strength."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors

def validate_phone_format(phone):
    """Validate phone number format."""
    # Basic validation - allow digits, spaces, hyphens, parentheses, and plus signs
    pattern = r'^[\d\s\-\(\)\+]+$'
    return re.match(pattern, phone) is not None and len(re.sub(r'[^\d]', '', phone)) >= 10

def validate_json_input(data, schema_class):
    """Validate JSON input against a schema."""
    try:
        schema = schema_class()
        result = schema.load(data)
        return True, result, None
    except ValidationError as e:
        return False, None, e.messages
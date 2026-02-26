from flask_mail import Mail, Message
from flask import current_app, url_for
import secrets

mail = Mail()

class EmailService:
    @staticmethod
    def send_verification_email(student):
        token = secrets.token_urlsafe(32)
        student.verification_token = token

        verify_url = url_for('verify_email', token=token, _external=True)

        msg = Message(
            'Verify Your Email - AI Invigilator',
            recipients=[student.email]
        )
        msg.body = f'''Hello {student.name},

Please verify your email by clicking the link below:

{verify_url}

This link will expire in 24 hours.

If you didn't register, please ignore this email.
'''
        try:
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False

    @staticmethod
    def send_password_reset(invigilator_email, invigilator_name, reset_link):
        """Send password reset email to invigilator"""
        msg = Message(
            'Password Reset Request - AI Invigilator',
            recipients=[invigilator_email]
        )
        msg.body = f'''Hello {invigilator_name},

You have requested to reset your password for the AI Invigilator system.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
AI Invigilator Team
'''
        try:
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Password reset email error: {e}")
            return False

    @staticmethod
    def send_alert_email(invigilator_email, alert_data):
        msg = Message(
            f'Exam Alert: {alert_data["type"]}',
            recipients=[invigilator_email]
        )
        msg.body = f'''Alert detected during exam:

Student: {alert_data["student_name"]}
Exam: {alert_data["exam_name"]}
Alert Type: {alert_data["type"]}
Severity: {alert_data["severity"]}
Time: {alert_data["timestamp"]}

Description: {alert_data["description"]}
'''
        try:
            mail.send(msg)
            return True
        except:
            return False

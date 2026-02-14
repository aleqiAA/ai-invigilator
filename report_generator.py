from datetime import datetime
from database import ExamSession, Alert, Student
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io

class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_session_report(self, session_id):
        session = ExamSession.query.get(session_id)
        if not session:
            return None
        
        student = Student.query.get(session.student_id)
        alerts = Alert.query.filter_by(session_id=session_id).all()
        
        # Calculate duration
        duration = None
        if session.end_time and session.start_time:
            duration = (session.end_time - session.start_time).total_seconds() / 60
        
        # Group alerts by type
        alert_types = {}
        for alert in alerts:
            if alert.alert_type not in alert_types:
                alert_types[alert.alert_type] = 0
            alert_types[alert.alert_type] += 1
        
        # Calculate risk score (0-100)
        risk_score = self.calculate_risk_score(alerts)
        
        report = {
            'session_id': session.id,
            'student': {
                'name': student.name,
                'student_id': student.student_id,
                'email': student.email
            },
            'exam': {
                'name': session.exam_name,
                'start_time': session.start_time.strftime('%Y-%m-%d %H:%M:%S') if session.start_time else 'Not started',
                'end_time': session.end_time.strftime('%Y-%m-%d %H:%M:%S') if session.end_time else 'In Progress',
                'duration_minutes': round(duration, 2) if duration else None,
                'status': session.status
            },
            'alerts': {
                'total': len(alerts),
                'by_type': alert_types,
                'by_severity': {
                    'critical': len([a for a in alerts if a.severity == 'critical']),
                    'high': len([a for a in alerts if a.severity == 'high']),
                    'medium': len([a for a in alerts if a.severity == 'medium']),
                    'low': len([a for a in alerts if a.severity == 'low'])
                }
            },
            'risk_score': risk_score,
            'recommendation': self.get_recommendation(risk_score)
        }
        
        return report
    
    def calculate_risk_score(self, alerts):
        if not alerts:
            return 0
        
        severity_weights = {
            'critical': 25,
            'high': 15,
            'medium': 8,
            'low': 3
        }
        
        total_score = 0
        for alert in alerts:
            total_score += severity_weights.get(alert.severity, 0)
        
        # Cap at 100
        return min(total_score, 100)
    
    def get_recommendation(self, risk_score):
        if risk_score >= 75:
            return 'HIGH RISK - Manual review strongly recommended'
        elif risk_score >= 50:
            return 'MEDIUM RISK - Review recommended'
        elif risk_score >= 25:
            return 'LOW RISK - Minor concerns detected'
        else:
            return 'MINIMAL RISK - No significant issues'
    
    def export_report_json(self, session_id, filepath):
        report = self.generate_session_report(session_id)
        if report:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=4)
            return True
        return False
    
    def generate_pdf_report(self, session_id):
        report = self.generate_session_report(session_id)
        if not report:
            return None
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(1*inch, height - 1*inch, "AI Invigilator Exam Report")
        
        # Student Info
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, height - 1.5*inch, "Student Information")
        c.setFont("Helvetica", 10)
        c.drawString(1*inch, height - 1.8*inch, f"Name: {report['student']['name']}")
        c.drawString(1*inch, height - 2*inch, f"ID: {report['student']['student_id']}")
        c.drawString(1*inch, height - 2.2*inch, f"Email: {report['student']['email']}")
        
        # Exam Info
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, height - 2.7*inch, "Exam Information")
        c.setFont("Helvetica", 10)
        c.drawString(1*inch, height - 3*inch, f"Exam: {report['exam']['name']}")
        c.drawString(1*inch, height - 3.2*inch, f"Start: {report['exam']['start_time']}")
        c.drawString(1*inch, height - 3.4*inch, f"End: {report['exam']['end_time']}")
        c.drawString(1*inch, height - 3.6*inch, f"Duration: {report['exam']['duration_minutes']} min")
        
        # Risk Score
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, height - 4.1*inch, "Integrity Assessment")
        c.setFont("Helvetica", 10)
        c.drawString(1*inch, height - 4.4*inch, f"Risk Score: {report['risk_score']}/100")
        c.drawString(1*inch, height - 4.6*inch, f"Recommendation: {report['recommendation']}")
        
        # Alerts
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, height - 5.1*inch, "Alerts Summary")
        c.setFont("Helvetica", 10)
        c.drawString(1*inch, height - 5.4*inch, f"Total Alerts: {report['alerts']['total']}")
        c.drawString(1*inch, height - 5.6*inch, f"Critical: {report['alerts']['by_severity']['critical']}")
        c.drawString(1*inch, height - 5.8*inch, f"High: {report['alerts']['by_severity']['high']}")
        c.drawString(1*inch, height - 6*inch, f"Medium: {report['alerts']['by_severity']['medium']}")
        c.drawString(1*inch, height - 6.2*inch, f"Low: {report['alerts']['by_severity']['low']}")
        
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

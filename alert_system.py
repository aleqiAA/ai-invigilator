from datetime import datetime
from database import db, Alert
from config import Config

class AlertSystem:
    def __init__(self):
        self.alerts = []
        
    def create_alert(self, session_id, alert_type, severity, description, screenshot_path=None):
        alert = Alert(
            session_id=session_id,
            alert_type=alert_type,
            severity=severity,
            description=description,
            screenshot_path=screenshot_path,
            timestamp=datetime.utcnow()
        )
        db.session.add(alert)
        db.session.commit()

        self.alerts.append({
            'type': alert_type,
            'severity': severity,
            'description': description,
            'timestamp': alert.timestamp
        })

        return alert

    def check_phone_usage(self, phone_detected, session_id):
        if phone_detected:
            return self.create_alert(
                session_id,
                'phone_usage',
                Config.ALERT_CRITICAL,
                'Phone usage detected during exam'
            )
        return None

    def check_help_request(self, raised_hand_detected, session_id):
        if raised_hand_detected:
            return self.create_alert(
                session_id,
                'help_request',
                Config.ALERT_LOW,
                'Student raised hand requesting help'
            )
        return None
    
    def check_face_violations(self, face_count, session_id):
        if face_count == 0:
            return self.create_alert(
                session_id,
                'no_face_detected',
                Config.ALERT_HIGH,
                'No face detected in frame'
            )
        elif face_count > 1:
            return self.create_alert(
                session_id,
                'multiple_faces',
                Config.ALERT_CRITICAL,
                f'{face_count} faces detected in frame'
            )
        return None
    
    def check_gaze_violation(self, is_looking_at_screen, session_id):
        if not is_looking_at_screen:
            return self.create_alert(
                session_id,
                'looking_away',
                Config.ALERT_MEDIUM,
                'Student looking away from screen'
            )
        return None
    
    def check_audio_violation(self, audio_detected, session_id):
        if audio_detected:
            return self.create_alert(
                session_id,
                'suspicious_audio',
                Config.ALERT_MEDIUM,
                'Suspicious audio activity detected'
            )
        return None
    
    def check_tab_switch(self, session_id):
        return self.create_alert(
            session_id,
            'tab_switch',
            Config.ALERT_HIGH,
            'Student switched tabs or lost focus'
        )
    
    def get_session_alerts(self, session_id):
        return Alert.query.filter_by(session_id=session_id).all()
    
    def get_alert_summary(self, session_id):
        alerts = self.get_session_alerts(session_id)
        summary = {
            'total': len(alerts),
            'critical': len([a for a in alerts if a.severity == Config.ALERT_CRITICAL]),
            'high': len([a for a in alerts if a.severity == Config.ALERT_HIGH]),
            'medium': len([a for a in alerts if a.severity == Config.ALERT_MEDIUM]),
            'low': len([a for a in alerts if a.severity == Config.ALERT_LOW])
        }
        return summary

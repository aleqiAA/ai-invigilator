import threading
from datetime import datetime, timedelta
from database import db, Alert
from config import Config


# ─────────────────────────────────────────────────────────────────────────────
# Cooldown settings (seconds) per alert type.
# Prevents alert spam when monitors fire repeatedly for the same violation.
# e.g. "looking_away" won't create a new alert if one was created < 30s ago.
# ─────────────────────────────────────────────────────────────────────────────
ALERT_COOLDOWNS = {
    'no_face_detected':  15,   # Check every 15s — brief camera dropout is common
    'multiple_faces':    10,   # Flag quickly but not every frame
    'looking_away':      30,   # Student might glance away momentarily
    'phone_usage':       20,   # Important but don't flood
    'help_request':       0,   # Always create — student is asking for help
    'tab_switch':         0,   # Always create — every switch matters
    'suspicious_audio':  20,   # Audio spikes can be brief
    'auto_submit':        0,   # One-time event
    'camera_issue':       0,   # One-time event
    'manual_flag':        0,   # Invigilator action — always create
}

DEFAULT_COOLDOWN = 20  # Fallback for any alert type not listed above


class AlertSystem:
    def __init__(self):
        # Per-session cooldown tracking: {session_id: {alert_type: last_fired_datetime}}
        self._cooldowns: dict[int, dict[str, datetime]] = {}
        self._lock = threading.Lock()

    # ──────────────────────────────────────────────────────────────────────
    # Core alert creation
    # ──────────────────────────────────────────────────────────────────────

    def create_alert(self, session_id, alert_type, severity, description, screenshot_path=None):
        """
        Create an alert if the cooldown period for this alert type has passed.
        Thread-safe. Returns the Alert object if created, or None if suppressed.
        """
        if not self._check_cooldown(session_id, alert_type):
            return None  # Too soon — suppressed to avoid spam

        alert = Alert(
            session_id=session_id,
            alert_type=alert_type,
            severity=severity,
            description=description,
            screenshot_path=screenshot_path,
            timestamp=datetime.utcnow()
        )

        try:
            db.session.add(alert)
            db.session.commit()
            self._update_cooldown(session_id, alert_type)
            return alert
        except Exception as e:
            db.session.rollback()
            print(f"[AlertSystem] Failed to save alert ({alert_type}): {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────
    # Monitor check methods — called by app.py routes and monitor callbacks
    # ──────────────────────────────────────────────────────────────────────

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

    # ──────────────────────────────────────────────────────────────────────
    # Callbacks — used by AudioMonitor and ScreenMonitor background threads
    # Pass these to monitor.start_session(session_id, alert_callback=...)
    # ──────────────────────────────────────────────────────────────────────

    def audio_alert_callback(self, session_id, event):
        """
        Called automatically by AudioMonitor background thread.
        Connects AudioMonitor directly to AlertSystem.
        """
        alert_type = event.get('type', 'suspicious_audio')
        level = event.get('level', 'N/A')

        if alert_type == 'sustained_noise':
            description = f"Sustained background noise detected (ratio: {event.get('ratio', 'N/A')})"
        else:
            description = f"Suspicious audio detected (level: {level})"

        self.check_audio_violation(True, session_id)

    def screen_alert_callback(self, session_id, event, count):
        """
        Called automatically by ScreenMonitor when focus is lost.
        Connects ScreenMonitor directly to AlertSystem.
        """
        event_type = event.get('type', 'tab_switch')

        if event_type == 'tab_switch':
            self.check_tab_switch(session_id)
        elif event_type == 'window_blur':
            self.create_alert(
                session_id,
                'window_blur',
                Config.ALERT_HIGH if count >= 5 else Config.ALERT_MEDIUM,
                f'Student lost window focus (total: {count} times)'
            )

    # ──────────────────────────────────────────────────────────────────────
    # Session lifecycle
    # ──────────────────────────────────────────────────────────────────────

    def register_session(self, session_id):
        """Call when an exam starts to initialise cooldown tracking."""
        with self._lock:
            self._cooldowns[session_id] = {}

    def clear_session(self, session_id):
        """Call when an exam ends to free cooldown memory."""
        with self._lock:
            self._cooldowns.pop(session_id, None)

    # ──────────────────────────────────────────────────────────────────────
    # Reporting
    # ──────────────────────────────────────────────────────────────────────

    def get_session_alerts(self, session_id):
        return Alert.query.filter_by(session_id=session_id).order_by(Alert.timestamp.desc()).all()

    def get_alert_summary(self, session_id):
        alerts = self.get_session_alerts(session_id)
        return {
            'total':    len(alerts),
            'critical': len([a for a in alerts if a.severity == Config.ALERT_CRITICAL]),
            'high':     len([a for a in alerts if a.severity == Config.ALERT_HIGH]),
            'medium':   len([a for a in alerts if a.severity == Config.ALERT_MEDIUM]),
            'low':      len([a for a in alerts if a.severity == Config.ALERT_LOW])
        }

    # ──────────────────────────────────────────────────────────────────────
    # Internal cooldown helpers
    # ──────────────────────────────────────────────────────────────────────

    def _check_cooldown(self, session_id, alert_type) -> bool:
        """
        Returns True if enough time has passed to create a new alert.
        Returns False if the alert should be suppressed (cooldown active).
        """
        cooldown_seconds = ALERT_COOLDOWNS.get(alert_type, DEFAULT_COOLDOWN)

        # Zero cooldown = always allow (e.g. help_request, tab_switch)
        if cooldown_seconds == 0:
            return True

        with self._lock:
            session_cooldowns = self._cooldowns.get(session_id, {})
            last_fired = session_cooldowns.get(alert_type)

        if last_fired is None:
            return True  # Never fired before — allow

        elapsed = (datetime.utcnow() - last_fired).total_seconds()
        return elapsed >= cooldown_seconds

    def _update_cooldown(self, session_id, alert_type):
        """Record when an alert was last successfully created."""
        with self._lock:
            if session_id not in self._cooldowns:
                self._cooldowns[session_id] = {}
            self._cooldowns[session_id][alert_type] = datetime.utcnow()
import threading
import time
from collections import deque
from datetime import datetime


class ScreenSessionMonitor:
    """
    Tracks screen/tab focus events for a single exam session.
    Each student gets their own isolated, thread-safe instance.
    """

    def __init__(self, session_id, alert_callback=None, tab_switch_threshold=3):
        self.session_id = session_id
        self.alert_callback = alert_callback
        self.tab_switch_threshold = tab_switch_threshold

        # Thread-safe state
        self._lock = threading.Lock()

        # Event history (capped to prevent unbounded memory growth)
        self._focus_events = deque(maxlen=500)
        self._tab_switch_count = 0
        self._window_blur_count = 0
        self._is_focused = True
        self._last_focus_time = datetime.utcnow()
        self._total_focus_lost_duration = 0.0  # seconds

    # ──────────────────────────────────────────────
    # Event handlers (called from Flask routes)
    # ──────────────────────────────────────────────

    def detect_tab_switch(self):
        """
        Call this when the student switches to another browser tab.
        Thread-safe — can be called from any thread.
        """
        now = datetime.utcnow()
        event = {
            'timestamp': now.isoformat(),
            'type': 'tab_switch',
            'session_id': self.session_id
        }

        with self._lock:
            self._tab_switch_count += 1
            self._is_focused = False
            self._focus_events.append(event)
            count = self._tab_switch_count

        # Fire alert callback outside the lock to prevent deadlocks
        if self.alert_callback and count >= self.tab_switch_threshold:
            threading.Thread(
                target=self.alert_callback,
                args=(self.session_id, event, count),
                daemon=True
            ).start()

    def detect_window_blur(self):
        """
        Call this when the browser window loses focus (alt-tab, etc.).
        Thread-safe.
        """
        now = datetime.utcnow()
        event = {
            'timestamp': now.isoformat(),
            'type': 'window_blur',
            'session_id': self.session_id
        }

        with self._lock:
            self._window_blur_count += 1
            self._is_focused = False
            self._focus_events.append(event)

        if self.alert_callback:
            threading.Thread(
                target=self.alert_callback,
                args=(self.session_id, event, self._window_blur_count),
                daemon=True
            ).start()

    def detect_window_focus(self):
        """
        Call this when the student returns focus to the exam window.
        Calculates how long they were away. Thread-safe.
        """
        now = datetime.utcnow()

        with self._lock:
            if not self._is_focused:
                # Calculate how long focus was lost
                duration = (now - self._last_focus_time).total_seconds()
                self._total_focus_lost_duration += duration

            self._is_focused = True
            self._last_focus_time = now
            self._focus_events.append({
                'timestamp': now.isoformat(),
                'type': 'window_focus',
                'session_id': self.session_id
            })

    def get_statistics(self):
        """Return a thread-safe snapshot of this session's screen activity."""
        with self._lock:
            return {
                'session_id': self.session_id,
                'total_tab_switches': self._tab_switch_count,
                'total_window_blurs': self._window_blur_count,
                'is_focused': self._is_focused,
                'total_focus_lost_seconds': round(self._total_focus_lost_duration, 1),
                'focus_lost_count': self._tab_switch_count + self._window_blur_count,
                'recent_events': list(self._focus_events)[-20:]  # Last 20 events
            }

    def reset(self):
        """Reset all counters for this session. Thread-safe."""
        with self._lock:
            self._tab_switch_count = 0
            self._window_blur_count = 0
            self._focus_events.clear()
            self._is_focused = True
            self._total_focus_lost_duration = 0.0
            self._last_focus_time = datetime.utcnow()


class ScreenMonitor:
    """
    Manager that owns one ScreenSessionMonitor per active exam session.
    Replaces the old single-instance ScreenMonitor in app.py.

    Usage in app.py:
        screen_monitor = ScreenMonitor()

        # When exam starts:
        screen_monitor.start_session(session_id, alert_callback=my_alert_fn)

        # From Flask route /tab_switch:
        screen_monitor.tab_switch(session_id)

        # From Flask route /window_blur:
        screen_monitor.window_blur(session_id)

        # From Flask route /window_focus:
        screen_monitor.window_focus(session_id)

        # When exam ends:
        screen_monitor.stop_session(session_id)
    """

    def __init__(self, tab_switch_threshold=3):
        self.tab_switch_threshold = tab_switch_threshold
        self._sessions: dict[int, ScreenSessionMonitor] = {}
        self._lock = threading.Lock()

    def start_session(self, session_id: int, alert_callback=None):
        """Register a new exam session for monitoring."""
        with self._lock:
            if session_id in self._sessions:
                return
            self._sessions[session_id] = ScreenSessionMonitor(
                session_id=session_id,
                alert_callback=alert_callback,
                tab_switch_threshold=self.tab_switch_threshold
            )

    def stop_session(self, session_id: int):
        """Remove a finished session from monitoring."""
        with self._lock:
            self._sessions.pop(session_id, None)

    def tab_switch(self, session_id: int):
        """Route a tab switch event to the correct session."""
        monitor = self._get_session(session_id)
        if monitor:
            monitor.detect_tab_switch()

    def window_blur(self, session_id: int):
        """Route a window blur event to the correct session."""
        monitor = self._get_session(session_id)
        if monitor:
            monitor.detect_window_blur()

    def window_focus(self, session_id: int):
        """Route a window focus event to the correct session."""
        monitor = self._get_session(session_id)
        if monitor:
            monitor.detect_window_focus()

    def get_statistics(self, session_id: int):
        """Get stats for a specific session."""
        monitor = self._get_session(session_id)
        return monitor.get_statistics() if monitor else {'error': 'Session not found'}

    def get_all_statistics(self):
        """Get stats for all active sessions."""
        with self._lock:
            session_ids = list(self._sessions.keys())
        return {sid: self._sessions[sid].get_statistics() for sid in session_ids}

    def _get_session(self, session_id: int):
        """Thread-safe session lookup."""
        with self._lock:
            return self._sessions.get(session_id)
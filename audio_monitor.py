import numpy as np
import threading
import time
from collections import deque
from datetime import datetime


class AudioSessionMonitor:
    """
    Monitors audio for a single exam session.
    Each student gets their own isolated instance with thread-safe state.
    """

    def __init__(self, session_id, alert_callback=None, threshold=0.5, window_seconds=3):
        self.session_id = session_id
        self.threshold = threshold
        self.alert_callback = alert_callback  # Called when suspicious audio is detected

        # Thread-safe state
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._monitor_thread = None

        # Audio event history (thread-safe deque with max length)
        self._audio_events = deque(maxlen=200)
        self._suspicious_count = 0
        self._is_monitoring = False

        # Rolling window: accumulate audio levels over N seconds before deciding
        self._window_seconds = window_seconds
        self._level_buffer = deque(maxlen=100)  # ~100 audio chunks per window

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def start_monitoring(self):
        """Start background monitoring thread for this session."""
        with self._lock:
            if self._is_monitoring:
                return  # Already running
            self._is_monitoring = True
            self._stop_event.clear()

        self._monitor_thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"audio-session-{self.session_id}",
            daemon=True  # Thread dies automatically if main process exits
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Gracefully stop the monitoring thread."""
        self._stop_event.set()

        with self._lock:
            self._is_monitoring = False

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=3)  # Wait up to 3s for clean exit

    def process_audio_chunk(self, audio_data: bytes):
        """
        Process a raw audio chunk received from the browser (WebAudio API).
        Call this from your Flask route whenever audio data arrives.
        Thread-safe — can be called from any thread.
        """
        level = self._calculate_rms(audio_data)

        with self._lock:
            self._level_buffer.append(level)

            if level > self.threshold:
                event = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': round(level, 4),
                    'type': 'voice_detected',
                    'session_id': self.session_id
                }
                self._audio_events.append(event)
                self._suspicious_count += 1

                # Fire callback immediately for real-time alerting
                if self.alert_callback:
                    threading.Thread(
                        target=self.alert_callback,
                        args=(self.session_id, event),
                        daemon=True
                    ).start()

                return True, level

        return False, level

    def get_status(self):
        """Return a snapshot of current monitoring state. Thread-safe."""
        with self._lock:
            recent_levels = list(self._level_buffer)
            avg_level = round(sum(recent_levels) / len(recent_levels), 4) if recent_levels else 0
            return {
                'session_id': self.session_id,
                'is_monitoring': self._is_monitoring,
                'suspicious_count': self._suspicious_count,
                'average_level': avg_level,
                'peak_level': round(max(recent_levels), 4) if recent_levels else 0,
                'recent_events': list(self._audio_events)[-10:]  # Last 10 events
            }

    # ──────────────────────────────────────────────
    # Internal methods
    # ──────────────────────────────────────────────

    def _heartbeat_loop(self):
        """
        Background thread: periodically checks if audio levels have
        been consistently suspicious over the rolling window.
        This catches sustained noise that individual chunk checks might miss.
        """
        while not self._stop_event.is_set():
            time.sleep(self._window_seconds)

            with self._lock:
                if not self._level_buffer:
                    continue
                levels = list(self._level_buffer)

            # If more than 40% of recent chunks are above threshold, flag it
            above_threshold = sum(1 for l in levels if l > self.threshold)
            ratio = above_threshold / len(levels)

            if ratio > 0.4 and self.alert_callback:
                event = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'type': 'sustained_noise',
                    'ratio': round(ratio, 2),
                    'session_id': self.session_id
                }
                threading.Thread(
                    target=self.alert_callback,
                    args=(self.session_id, event),
                    daemon=True
                ).start()

    @staticmethod
    def _calculate_rms(audio_data: bytes) -> float:
        """Calculate normalized RMS level from raw PCM audio bytes."""
        if not audio_data:
            return 0.0
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            if len(audio_array) == 0:
                return 0.0
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            return float(rms / 32768.0)  # Normalize to 0.0–1.0
        except Exception:
            return 0.0


class AudioMonitor:
    """
    Manager class that owns one AudioSessionMonitor per active exam session.
    Replaces the old single-instance AudioMonitor in app.py.

    Usage in app.py:
        audio_monitor = AudioMonitor()

        # When exam starts:
        audio_monitor.start_session(session_id, alert_callback=my_alert_fn)

        # When audio data arrives from browser:
        audio_monitor.process_chunk(session_id, raw_bytes)

        # When exam ends:
        audio_monitor.stop_session(session_id)
    """

    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self._sessions: dict[int, AudioSessionMonitor] = {}
        self._lock = threading.Lock()

    def start_session(self, session_id: int, alert_callback=None):
        """Create and start a monitor for a new exam session."""
        with self._lock:
            if session_id in self._sessions:
                return  # Already exists
            monitor = AudioSessionMonitor(
                session_id=session_id,
                alert_callback=alert_callback,
                threshold=self.threshold
            )
            self._sessions[session_id] = monitor

        monitor.start_monitoring()

    def stop_session(self, session_id: int):
        """Stop and clean up the monitor for a finished session."""
        with self._lock:
            monitor = self._sessions.pop(session_id, None)

        if monitor:
            monitor.stop_monitoring()

    def process_chunk(self, session_id: int, audio_data: bytes):
        """Route an audio chunk to the correct session monitor."""
        with self._lock:
            monitor = self._sessions.get(session_id)

        if monitor:
            return monitor.process_audio_chunk(audio_data)
        return False, 0.0

    def get_status(self, session_id: int):
        """Get status for a specific session."""
        with self._lock:
            monitor = self._sessions.get(session_id)
        return monitor.get_status() if monitor else {'error': 'Session not found'}

    def get_all_statuses(self):
        """Get status for all active sessions (useful for dashboard)."""
        with self._lock:
            session_ids = list(self._sessions.keys())
        return {sid: self._sessions[sid].get_status() for sid in session_ids}
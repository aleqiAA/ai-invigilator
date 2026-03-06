"""
AI Invigilator — Risk Scoring Engine v2
========================================
Three-layer ensemble scoring system.

Layer 1 — Weighted feature scoring (50%)
    Calibrated per violation type + severity + time decay.

Layer 2 — Cohort anomaly detection (30%)
    Isolation Forest comparing student vs peers.
    Falls back to population norms when < 4 peers.

Layer 3 — Temporal pattern analysis (20%)
    Rhythmic violations, co-occurrence, acceleration bursts.

Output: 0-100 risk score, confidence, full breakdown.
"""

import math
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from typing import Optional

import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import RobustScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not installed. Run: pip install scikit-learn numpy")

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# CALIBRATED VIOLATION WEIGHTS  (0.0 = benign → 1.0 = definitive)
# ─────────────────────────────────────────────────────────────
VIOLATION_WEIGHTS = {
    'tab_switch':               0.50,
    'fullscreen_exit':          0.42,
    'window_blur':              0.18,
    'window_focus':             0.00,
    'devtools_detected':        0.85,
    'multiple_monitors':        0.65,
    'screen_sharing':           0.92,
    'view_source_attempt':      0.72,
    'screenshot_attempt':       0.78,
    'copy_attempt':             0.38,
    'paste_attempt':            0.42,
    'face_absent':              0.52,
    'face_multiple':            0.88,
    'face_looking_away':        0.32,
    'face_covered':             0.72,
    'no_camera':                0.22,
    'network_anomaly':          0.55,
    'rapid_answers':            0.60,
    'session_resume':           0.12,
    'camera_issue':             0.08,
    'help_requested':           0.03,
    '_default':                 0.28,
}

SEVERITY_MULTIPLIERS = {
    'critical': 2.2,
    'high':     1.6,
    'medium':   1.0,
    'low':      0.55,
}

DECAY_HALF_LIFE_MINUTES = 18.0

POPULATION_BASELINE = {
    'mean_weighted_score': 0.4,
    'std_weighted_score':  0.6,
    'mean_tab_rate':       0.05,
}


# ─────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────
def _now():
    return datetime.now(timezone.utc)


def _parse_ts(ts, fallback=None):
    if fallback is None:
        fallback = _now()
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return fallback


# ─────────────────────────────────────────────────────────────
# FEATURE EXTRACTOR  — 17-dimension vector
# ─────────────────────────────────────────────────────────────
class FeatureExtractor:

    FEATURE_NAMES = [
        'total_violations', 'raw_weighted_score',
        'critical_count', 'high_count',
        'tab_switch_count', 'tab_rate_per_min', 'fullscreen_exit_count',
        'face_absence_ratio', 'devtools_count', 'copy_paste_count',
        'screen_share_count', 'burst_2min', 'burst_5min',
        'answer_speed', 'session_completion',
        'violation_acceleration', 'unique_types',
    ]

    def extract(self, sd: dict) -> np.ndarray:
        alerts   = sd.get('alerts', [])
        duration = sd.get('duration_minutes', 60) * 60
        elapsed  = sd.get('elapsed_seconds', 0)
        answers  = sd.get('answer_count', 0)
        now      = _now()

        emin = max(elapsed / 60.0, 0.5)
        tc   = Counter(a.get('alert_type', '_default') for a in alerts)
        sc   = Counter(a.get('severity', 'low') for a in alerts)

        raw_w = sum(
            VIOLATION_WEIGHTS.get(a.get('alert_type', '_default'), 0.28)
            * SEVERITY_MULTIPLIERS.get(a.get('severity', 'medium'), 1.0)
            for a in alerts
        )
        face_ratio = min(1.0, (tc.get('face_absent', 0) + tc.get('face_covered', 0)) * 5 / max(elapsed, 1))

        v = np.array([
            len(alerts),
            raw_w,
            sc.get('critical', 0),
            sc.get('high', 0),
            tc.get('tab_switch', 0),
            tc.get('tab_switch', 0) / emin,
            tc.get('fullscreen_exit', 0),
            face_ratio,
            tc.get('devtools_detected', 0),
            tc.get('copy_attempt', 0) + tc.get('paste_attempt', 0),
            tc.get('screen_sharing', 0),
            self._burst(alerts, 2),
            self._burst(alerts, 5),
            answers / emin,
            min(1.0, elapsed / max(duration, 1)),
            self._acceleration(alerts),
            float(len(set(a.get('alert_type') for a in alerts))),
        ], dtype=np.float32)
        return np.nan_to_num(v, nan=0.0, posinf=10.0)

    def _burst(self, alerts, window_min):
        if not alerts:
            return 0.0
        now   = _now()
        times = sorted(_parse_ts(a.get('timestamp', now)) for a in alerts)
        win   = timedelta(minutes=window_min)
        best  = 0
        for i, t in enumerate(times):
            count = sum(1 for t2 in times[i:] if t2 - t <= win)
            best  = max(best, count)
        return float(best)

    def _acceleration(self, alerts):
        if len(alerts) < 4:
            return 0.0
        now    = _now()
        counts = defaultdict(int)
        for a in alerts:
            age = max(0, (now - _parse_ts(a.get('timestamp', now))).total_seconds())
            counts[int(age // 300)] += 1
        if len(counts) < 2:
            return 0.0
        slots  = sorted(counts.keys(), reverse=True)
        values = [counts[s] for s in slots]
        x      = np.arange(len(values), dtype=np.float32)
        try:
            return float(np.clip(np.polyfit(x, values, 1)[0], -5, 5))
        except Exception:
            return 0.0


# ─────────────────────────────────────────────────────────────
# COHORT ANOMALY DETECTOR
# ─────────────────────────────────────────────────────────────
class CohortAnomalyDetector:
    MIN_SESSIONS = 4

    def __init__(self):
        self._cache: dict = {}

    def fit(self, matrix: np.ndarray, key: str) -> bool:
        if len(matrix) < self.MIN_SESSIONS or not SKLEARN_AVAILABLE:
            return False
        try:
            scaler = RobustScaler()
            X      = scaler.fit_transform(matrix)
            model  = IsolationForest(
                n_estimators=300, contamination=0.15,
                max_samples=min(len(matrix), 256),
                random_state=42, n_jobs=-1,
            )
            model.fit(X)
            self._cache[key] = (model, scaler)
            return True
        except Exception as e:
            logger.warning(f"Cohort fit error: {e}")
            return False

    def score(self, features: np.ndarray, key: str) -> float:
        entry = self._cache.get(key)
        if entry is None:
            return self._population_fallback(features)
        model, scaler = entry
        try:
            X   = scaler.transform(features.reshape(1, -1))
            raw = model.score_samples(X)[0]
            # map [-0.8, -0.2] → [100, 0]
            return float(np.clip((-raw - 0.2) / 0.6, 0, 1) * 100)
        except Exception:
            return 50.0

    def _population_fallback(self, f: np.ndarray) -> float:
        ws  = float(f[1])  # raw_weighted_score
        tr  = float(f[5])  # tab_rate
        z1  = (ws  - 0.4) / 0.6
        z2  = (tr  - 0.05) / 0.1
        s   = np.clip((z1 * 0.7 + z2 * 0.3) / 3.0, 0, 1) * 100
        return float(s)


# ─────────────────────────────────────────────────────────────
# PATTERN ANALYSER
# ─────────────────────────────────────────────────────────────
class PatternAnalyser:

    def score(self, alerts: list) -> tuple:
        if len(alerts) < 2:
            return 0.0, []

        now      = _now()
        findings = []
        score    = 0.0

        events = sorted([{
            'type':     a.get('alert_type', ''),
            'severity': a.get('severity', 'low'),
            'time':     _parse_ts(a.get('timestamp', now)),
        } for a in alerts], key=lambda e: e['time'])

        # P1: Rhythmic tab switches
        tab_t = [e['time'] for e in events if e['type'] == 'tab_switch']
        if len(tab_t) >= 3:
            ivs = [(tab_t[i+1]-tab_t[i]).total_seconds() for i in range(len(tab_t)-1)]
            if ivs:
                cv = np.std(ivs) / (np.mean(ivs) + 1e-9)
                if cv < 0.30 and np.mean(ivs) < 180:
                    score += 30
                    findings.append(f"Rhythmic tab switching ×{len(tab_t)} (regularity {1-cv:.0%})")

        # P2: Clipboard automation cluster
        clip_t = [e['time'] for e in events if e['type'] in ('copy_attempt','paste_attempt')]
        if len(clip_t) >= 3:
            for i in range(len(clip_t)-2):
                w = (clip_t[i+2]-clip_t[i]).total_seconds()
                if w < 45:
                    score += 28
                    findings.append(f"Clipboard automation: 3 attempts in {w:.0f}s")
                    break

        # P3: Face disappears with tab switches
        face_t = [e['time'] for e in events if e['type'] == 'face_absent']
        tab_t2 = [e['time'] for e in events if e['type'] == 'tab_switch']
        if face_t and tab_t2:
            co = sum(1 for ft in face_t for tt in tab_t2 if abs((ft-tt).total_seconds()) < 8)
            if co >= 2:
                score += 30
                findings.append(f"Face disappears alongside tab switches ×{co}")

        # P4: Severity escalation
        sev_map = {'low':1,'medium':2,'high':3,'critical':4}
        sv = [sev_map.get(e['severity'],1) for e in events]
        if len(sv) >= 6:
            mid = len(sv)//2
            if np.mean(sv[mid:]) > np.mean(sv[:mid]) * 1.4:
                score += 18
                findings.append("Alert severity escalating over exam duration")

        # P5: High-risk in last 10 minutes
        hrt = {'screen_sharing','devtools_detected','face_multiple','screenshot_attempt'}
        recent = [e for e in events if e['type'] in hrt and (now-e['time']).total_seconds() < 600]
        if len(recent) >= 2:
            score += 25
            findings.append(f"{len(recent)} high-risk events in last 10 minutes")

        # P6: Burst after calm period
        if len(events) >= 5:
            times = [e['time'] for e in events]
            gaps  = [(times[i+1]-times[i]).total_seconds() for i in range(len(times)-1)]
            if max(gaps) > 300:
                idx   = gaps.index(max(gaps))
                after = events[idx+1:]
                if len(after) >= 3:
                    w = (after[-1]['time']-after[0]['time']).total_seconds()
                    if w < 120:
                        score += 20
                        findings.append("Sudden violation burst after calm period")

        return min(100.0, score), findings


# ─────────────────────────────────────────────────────────────
# RISK SCORER — main interface
# ─────────────────────────────────────────────────────────────
class RiskScorer:
    """Instantiate once, reuse across requests."""

    LAYER_WEIGHTS = {'violations': 0.50, 'cohort': 0.30, 'patterns': 0.20}

    def __init__(self):
        self.extractor = FeatureExtractor()
        self.anomaly   = CohortAnomalyDetector()
        self.pattern   = PatternAnalyser()

    def score_session(self, sd: dict, exam_key: str = '') -> dict:
        alerts  = sd.get('alerts', [])
        elapsed = sd.get('elapsed_seconds', 0)

        features     = self.extractor.extract(sd)
        l1           = self._violation_score(alerts)
        l2           = self.anomaly.score(features, exam_key)
        l3, findings = self.pattern.score(alerts)

        w     = self.LAYER_WEIGHTS
        final = int(round(np.clip(l1*w['violations'] + l2*w['cohort'] + l3*w['patterns'], 0, 100)))

        return {
            'score':       final,
            'level':       self._level(final),
            'confidence':  round(self._confidence(len(alerts), elapsed), 2),
            'breakdown':   {'violations': round(l1), 'cohort': round(l2), 'patterns': round(l3)},
            'findings':    findings,
            'explanation': self._explain(final, l1, l2, l3, alerts, findings),
            'features':    features.tolist(),
        }

    def score_exam(self, sessions: list) -> list:
        if not sessions:
            return []
        key = sessions[0].get('exam_name', 'unknown')
        if len(sessions) >= CohortAnomalyDetector.MIN_SESSIONS and SKLEARN_AVAILABLE:
            matrix = np.array([self.extractor.extract(s) for s in sessions])
            self.anomaly.fit(matrix, key)
        results = []
        for s in sessions:
            r = self.score_session(s, key)
            r.update({k: s.get(k) for k in ('session_id','student_name','student_id','exam_name')})
            results.append(r)
        results.sort(key=lambda r: r['score'], reverse=True)
        return results

    def _violation_score(self, alerts: list) -> float:
        if not alerts:
            return 0.0
        now = _now()
        total = 0.0
        for a in alerts:
            w     = VIOLATION_WEIGHTS.get(a.get('alert_type','_default'), 0.28)
            sm    = SEVERITY_MULTIPLIERS.get(a.get('severity','medium'), 1.0)
            age   = max(0, (now - _parse_ts(a.get('timestamp', now))).total_seconds() / 60)
            decay = math.exp(-math.log(2) * age / DECAY_HALF_LIFE_MINUTES)
            total += w * sm * decay
        return float(np.clip(total / 4.0, 0, 1) * 100)

    def _confidence(self, n: int, elapsed: int) -> float:
        return min(1.0, elapsed/600)*0.55 + min(1.0, n/4)*0.45

    def _level(self, s: int) -> str:
        if s >= 75: return 'critical'
        if s >= 50: return 'alert'
        if s >= 25: return 'watch'
        return 'low'

    def _explain(self, final, l1, l2, l3, alerts, findings) -> str:
        if final == 0:
            return "No violations detected. Session appears normal."
        drivers = sorted([('violation patterns',l1),('cohort comparison',l2),('timing patterns',l3)],
                         key=lambda x: x[1], reverse=True)
        tc  = Counter(a.get('alert_type') for a in alerts)
        top = tc.most_common(2)
        parts = [f"Driven by {drivers[0][0]}."]
        if top:
            parts.append("Most frequent: " + ", ".join(f"{k.replace('_',' ')} ×{v}" for k,v in top) + ".")
        if findings:
            parts.append(findings[0] + ".")
        return " ".join(parts)


# ─────────────────────────────────────────────────────────────
# FLASK HELPERS — import these in your app
# ─────────────────────────────────────────────────────────────
_scorer: Optional[RiskScorer] = None

def get_scorer() -> RiskScorer:
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer

def session_to_data(session, alerts) -> dict:
    now   = _now()
    start = session.start_time
    if start and getattr(start, 'tzinfo', None) is None:
        start = start.replace(tzinfo=timezone.utc)
    elapsed = int((now - start).total_seconds()) if start else 0
    return {
        'session_id':       session.id,
        'exam_name':        getattr(session, 'exam_name', ''),
        'student_id':       session.student.student_id if session.student else '',
        'student_name':     session.student.name if session.student else '',
        'start_time':       start,
        'duration_minutes': getattr(session, 'duration_minutes', 60),
        'elapsed_seconds':  elapsed,
        'answer_count':     len(getattr(session, 'answers', [])),
        'total_questions':  getattr(session, 'total_questions', 10),
        'alerts': [{
            'alert_type': getattr(a, 'alert_type', 'unknown'),
            'severity':   getattr(a, 'severity', 'low'),
            'timestamp':  getattr(a, 'timestamp', now),
        } for a in alerts],
    }

def score_single(session, alerts) -> dict:
    """Score one session. Call from any Flask route."""
    data = session_to_data(session, alerts)
    return get_scorer().score_session(data, data['exam_name'])

def score_all(active_sessions, alerts_by_session: dict) -> list:
    """Score all sessions with cohort comparison. alerts_by_session = {id: [Alert]}"""
    sessions = [session_to_data(s, alerts_by_session.get(s.id, [])) for s in active_sessions]
    return get_scorer().score_exam(sessions)
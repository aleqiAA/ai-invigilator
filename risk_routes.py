"""
AI Invigilator — Risk Scoring API Routes
==========================================
Add to your Flask app:

    from risk_routes import register_risk_routes
    register_risk_routes(app, db, ExamSession, Alert)
"""

from flask import jsonify, request
from datetime import datetime, timezone
from collections import defaultdict


def register_risk_routes(app, db, ExamSession, Alert):
    """
    Call once in your app factory / main app.py:

        register_risk_routes(app, db, ExamSession, Alert)
    """

    # Import here so it doesn't fail if scikit-learn isn't installed yet
    from risk_scorer import score_single, score_all, get_scorer, session_to_data

    # ── GET /api/risk/session/<id> ────────────────────────────
    @app.route('/api/risk/session/<int:session_id>')
    def api_risk_session(session_id):
        """Score a single exam session."""
        session = ExamSession.query.get_or_404(session_id)
        alerts  = Alert.query.filter_by(session_id=session_id).all()
        result  = score_single(session, alerts)
        return jsonify(result)

    # ── GET /api/risk/exam/<name> ─────────────────────────────
    @app.route('/api/risk/exam/<path:exam_name>')
    def api_risk_exam(exam_name):
        """Score all sessions for an exam — enables cohort comparison."""
        sessions = ExamSession.query.filter_by(exam_name=exam_name).all()
        if not sessions:
            return jsonify({'error': 'No sessions found', 'results': []}), 404

        # Bulk-load all alerts for these sessions in one query
        session_ids = [s.id for s in sessions]
        all_alerts  = Alert.query.filter(Alert.session_id.in_(session_ids)).all()
        by_session  = defaultdict(list)
        for a in all_alerts:
            by_session[a.session_id].append(a)

        results = score_all(sessions, by_session)
        return jsonify({
            'exam_name':   exam_name,
            'total':       len(results),
            'results':     results,
            'summary': {
                'critical': sum(1 for r in results if r['level'] == 'critical'),
                'alert':    sum(1 for r in results if r['level'] == 'alert'),
                'watch':    sum(1 for r in results if r['level'] == 'watch'),
                'low':      sum(1 for r in results if r['level'] == 'low'),
            }
        })

    # ── GET /api/risk/live ────────────────────────────────────
    @app.route('/api/risk/live')
    def api_risk_live():
        """
        Score all currently active sessions.
        Called every ~10s from the invigilator dashboard.
        """
        active_sessions = ExamSession.query.filter_by(status='active').all()
        if not active_sessions:
            return jsonify({'sessions': [], 'total': 0})

        session_ids = [s.id for s in active_sessions]
        all_alerts  = Alert.query.filter(Alert.session_id.in_(session_ids)).all()
        by_session  = defaultdict(list)
        for a in all_alerts:
            by_session[a.session_id].append(a)

        results = score_all(active_sessions, by_session)

        # Attach student name and strip heavy fields for the live feed
        lite = []
        for r in results:
            lite.append({
                'session_id':   r.get('session_id'),
                'student_name': r.get('student_name', ''),
                'student_id':   r.get('student_id', ''),
                'score':        r['score'],
                'level':        r['level'],
                'confidence':   r['confidence'],
                'breakdown':    r['breakdown'],
                'findings':     r['findings'][:2],   # top 2 only
                'explanation':  r['explanation'],
            })

        return jsonify({
            'sessions': lite,
            'total':    len(lite),
            'critical': sum(1 for r in lite if r['level'] == 'critical'),
            'alert':    sum(1 for r in lite if r['level'] == 'alert'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    # ── GET /api/risk/student/<student_id>/history ────────────
    @app.route('/api/risk/student/<student_id>/history')
    def api_risk_student_history(student_id):
        """Risk score history across all sessions for a student."""
        sessions = (ExamSession.query
                    .join(ExamSession.student)
                    .filter_by(student_id=student_id)
                    .order_by(ExamSession.start_time.desc())
                    .limit(10)
                    .all())

        history = []
        for s in sessions:
            alerts = Alert.query.filter_by(session_id=s.id).all()
            result = score_single(s, alerts)
            history.append({
                'exam_name':  s.exam_name,
                'date':       s.start_time.isoformat() if s.start_time else None,
                'score':      result['score'],
                'level':      result['level'],
                'alert_count': len(alerts),
            })

        return jsonify({
            'student_id': student_id,
            'history':    history,
            'avg_score':  round(sum(h['score'] for h in history) / len(history), 1) if history else 0,
        })

    return app
import json
from database import db, Answer, Question, ExamSession

class AutoGrader:
    @staticmethod
    def grade_answer(answer_id):
        """Grade a single answer (MCQ only)"""
        answer = Answer.query.get(answer_id)
        if not answer:
            return None
        
        question = answer.question
        
        # Only auto-grade multiple choice
        if question.question_type == 'multiple_choice':
            is_correct = answer.answer_text.strip().upper() == question.correct_answer.strip().upper()
            answer.is_correct = is_correct
            answer.points_earned = question.points if is_correct else 0
            db.session.commit()
            return {'is_correct': is_correct, 'points_earned': answer.points_earned}
        
        # Essay questions need manual grading
        return {'is_correct': None, 'points_earned': 0, 'needs_manual_grading': True}
    
    @staticmethod
    def grade_session(session_id):
        """Grade all answers in a session and calculate total score"""
        session = ExamSession.query.get(session_id)
        if not session:
            return None
        
        # Get all questions for this exam
        questions = Question.query.filter_by(exam_name=session.exam_name).all()
        max_score = sum(q.points for q in questions)
        
        # Get all answers for this session
        answers = Answer.query.filter_by(session_id=session_id).all()
        
        total_score = 0
        graded_count = 0
        needs_manual = 0
        
        for answer in answers:
            result = AutoGrader.grade_answer(answer.id)
            if result:
                if result.get('needs_manual_grading'):
                    needs_manual += 1
                else:
                    total_score += result['points_earned']
                    graded_count += 1
        
        # Update session scores
        session.total_score = total_score
        session.max_score = max_score
        db.session.commit()
        
        return {
            'total_score': total_score,
            'max_score': max_score,
            'percentage': round((total_score / max_score * 100) if max_score > 0 else 0, 2),
            'graded_count': graded_count,
            'needs_manual': needs_manual
        }
    
    @staticmethod
    def get_session_results(session_id):
        """Get detailed results for a session"""
        session = ExamSession.query.get(session_id)
        if not session:
            return None
        
        answers = Answer.query.filter_by(session_id=session_id).all()
        
        results = []
        for answer in answers:
            question = answer.question
            results.append({
                'question_id': question.id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'student_answer': answer.answer_text,
                'correct_answer': question.correct_answer if question.question_type == 'multiple_choice' else None,
                'is_correct': answer.is_correct,
                'points_earned': answer.points_earned,
                'max_points': question.points
            })
        
        return {
            'session_id': session_id,
            'student_name': session.student.name,
            'exam_name': session.exam_name,
            'total_score': session.total_score,
            'max_score': session.max_score,
            'percentage': round((session.total_score / session.max_score * 100) if session.max_score > 0 else 0, 2),
            'answers': results
        }

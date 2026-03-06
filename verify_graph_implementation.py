#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify Graph Question Implementation
Checks all components are in place
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("GRAPH QUESTION IMPLEMENTATION VERIFICATION")
print("=" * 80)

checks_passed = 0
checks_failed = 0

def check(description, condition, details=""):
    global checks_passed, checks_failed
    if condition:
        print(f"✓ {description}")
        if details:
            print(f"  {details}")
        checks_passed += 1
    else:
        print(f"✗ {description}")
        if details:
            print(f"  {details}")
        checks_failed += 1

# 1. Check database model
print("\n[1/6] Database Model")
try:
    from database import Question
    has_reference_image = hasattr(Question, 'reference_image')
    check("Question model has reference_image column", has_reference_image)
    if not has_reference_image:
        print("  → Run: python add_reference_image_column.py")
except Exception as e:
    check("Question model import", False, str(e))

# 2. Check exam.html template
print("\n[2/6] Student Exam Template (exam.html)")
try:
    with open('templates/exam.html', 'r', encoding='utf-8') as f:
        exam_content = f.read()
    
    check("Graph question type handling", '{% elif q.question_type == \'graph\' %}' in exam_content)
    check("Reference image display", 'q.reference_image' in exam_content)
    check("Show Reference button", 'toggleReferenceGraph' in exam_content)
    check("Reference graph panel", 'referenceGraph' in exam_content)
    check("GeoGebra iframe", 'geogebra.org/classic' in exam_content)
    check("Save Graph button", 'saveGraph' in exam_content)
    check("Auto-save function", 'setInterval' in exam_content and 'saveGraph' in exam_content)
    check("toggleReferenceGraph function", 'function toggleReferenceGraph' in exam_content)
except Exception as e:
    check("exam.html file", False, str(e))

# 3. Check view_answers.html template
print("\n[3/6] Invigilator Review Template (view_answers.html)")
try:
    with open('templates/view_answers.html', 'r', encoding='utf-8') as f:
        view_content = f.read()
    
    check("Graph answer display", 'question_type == \'graph\'' in view_content)
    check("Student graph image", '<img src="{{ answers[q.id].answer_text }}"' in view_content)
    check("Grading interface (graded)", 'answers[q.id].graded_at' in view_content)
    check("Grading interface (ungraded)", 'Needs Manual Grading' in view_content)
    check("Points input field", 'points_' in view_content)
    check("Feedback textarea", 'feedback_' in view_content)
    check("Submit Grade button", 'Submit Grade' in view_content)
    check("gradeEssay function call", 'gradeEssay(' in view_content)
except Exception as e:
    check("view_answers.html file", False, str(e))

# 4. Check manage_questions.html template
print("\n[4/6] Question Management Template (manage_questions.html)")
try:
    with open('templates/manage_questions.html', 'r', encoding='utf-8') as f:
        manage_content = f.read()
    
    check("Graph question type option", 'value="graph"' in manage_content)
    check("GeoGebra iframe", 'geogebraIframe' in manage_content)
    check("Capture Graph button", 'captureGraph' in manage_content)
    check("Graph preview", 'graphPreview' in manage_content)
    check("Hidden reference image input", 'graph_reference_image' in manage_content)
    check("Axis configuration fields", 'graph_x_min' in manage_content)
    check("Graph display in list", 'q.reference_image' in manage_content)
except Exception as e:
    check("manage_questions.html file", False, str(e))

# 5. Check backend routes
print("\n[5/6] Backend Routes (app.py)")
try:
    with open('app.py', 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    check("manage_questions route", '@app.route(\'/manage_questions/' in app_content)
    check("Graph reference image handling", 'reference_image = request.form.get(\'graph_reference_image\')' in app_content)
    check("Graph config JSON", 'graph_config' in app_content)
    check("Axis config parsing", 'graph_x_min' in app_content)
    check("Question reference_image save", 'reference_image=reference_image' in app_content)
    check("grade_essay route", '@app.route(\'/grade_essay\'' in app_content)
    check("submit_answer route", '@app.route(\'/submit_answer\'' in app_content)
except Exception as e:
    check("app.py file", False, str(e))

# 6. Check migration script
print("\n[6/6] Database Migration")
try:
    import os
    migration_exists = os.path.exists('add_reference_image_column.py')
    check("Migration script exists", migration_exists)
    if migration_exists:
        print("  File: add_reference_image_column.py")
except Exception as e:
    check("Migration script", False, str(e))

# Summary
print("\n" + "=" * 80)
print(f"VERIFICATION COMPLETE: {checks_passed} passed, {checks_failed} failed")
print("=" * 80)

if checks_failed > 0:
    print("\n⚠️  Some checks failed. Please review the items above.")
    if 'has_reference_image' in dir() and not has_reference_image:
        print("\nRequired action:")
        print("  python add_reference_image_column.py")
else:
    print("\n✅ All checks passed! Graph questions are fully implemented.")
    print("\nNext steps:")
    print("  1. Run: python app.py")
    print("  2. Visit: http://localhost:5000/manage_questions/TestExam")
    print("  3. Create a graph question with reference image")
    print("  4. Test student view and invigilator grading")

print("=" * 80)

# Exam Questions Feature - Setup Guide

## ⚠️ IMPORTANT: Database Reset Required

Since we added new database tables (Question and Answer), you MUST reset the database:

```bash
# 1. Stop the Flask app (Ctrl+C in terminal)

# 2. Delete the old database
del instance\invigilator.db

# 3. Restart the app (this creates new tables)
python app.py
```

## 📝 New Features Added

### For Invigilators:

1. **Manage Questions** (`/manage_questions/<exam_name>`)
   - Add essay questions (students type answers)
   - Add multiple choice questions (A, B, C, D options)
   - Set points for each question
   - Delete questions
   - Access from Exam Schedule page

2. **View Student Answers** (`/view_answers/<session_id>`)
   - See all student answers for completed exams
   - Multiple choice shows selected answer vs correct answer
   - Essay answers shown in full
   - Access from Sessions/Reports page

### For Students:

1. **Answer Questions During Exam**
   - Questions appear after starting exam
   - Essay questions: Type in text area (auto-saves)
   - Multiple choice: Select radio button (auto-saves)
   - Answers saved automatically as student types/selects
   - Can change answers anytime during exam

## 🎯 How to Use

### Step 1: Create Questions (Invigilator)

1. Login as invigilator
2. Go to "Exam Scheduling" page
3. Click "📝 Questions" link next to any exam
4. Add questions:
   - Choose "Essay" or "Multiple Choice"
   - Enter question text
   - For multiple choice: Add 4 options (A, B, C, D) and select correct answer
   - Set points
   - Click "Add Question"

### Step 2: Schedule Exam (Invigilator)

1. Schedule exam for student/cohort as usual
2. Questions are automatically linked to exam by exam name

### Step 3: Student Takes Exam

1. Student logs in and starts exam
2. After camera checks, questions appear below video feed
3. Student answers questions (auto-saved)
4. Student clicks "End Exam" when done

### Step 4: Review Answers (Invigilator)

1. Go to "Reports" page
2. Click "View Answers" button for any completed exam
3. See all questions and student answers
4. Multiple choice shows if answer was correct

## 📊 Database Schema

### Question Table
- exam_name: Links to ExamSession.exam_name
- question_text: The question
- question_type: 'essay' or 'multiple_choice'
- options: JSON string with A, B, C, D options (for MC only)
- correct_answer: 'A', 'B', 'C', or 'D' (for MC only)
- points: Point value
- order: Display order

### Answer Table
- session_id: Links to ExamSession
- question_id: Links to Question
- answer_text: Student's answer (essay text or 'A'/'B'/'C'/'D')
- submitted_at: Timestamp

## 🔗 New Routes

- `/manage_questions/<exam_name>` - Add/manage questions
- `/delete_question/<id>` - Delete a question
- `/submit_answer` - Save student answer (auto-called)
- `/view_answers/<session_id>` - View student answers

## 💡 Tips

- Create questions BEFORE scheduling the exam
- Questions are reusable - same exam name = same questions
- Students can change answers anytime during exam
- Answers auto-save every time student types or selects
- Multiple choice questions show correct answer to invigilator only

## 🌐 URLs

**Manage Questions:** `http://localhost:5000/manage_questions/<exam_name>`
**View Answers:** `http://localhost:5000/view_answers/<session_id>`

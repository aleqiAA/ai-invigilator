# Math, Graph & Programming Questions Implementation

## What Was Implemented

### 1. **Mathematical Questions with Calculator Support**
- Added `allow_calculator` field to Question model
- Added calculator whitelist in config.py (calc.exe, calculator, gnome-calculator, kcalc)
- Checkbox in question creation form to enable calculator for specific questions
- Badge displayed on exam page showing "Calculator Allowed"
- Students can use system calculator without triggering security alerts

### 2. **Graph/Plotting Questions**
- Uses existing essay question type + file upload capability
- Students can:
  - Draw graphs on paper → photograph → upload image
  - Describe graph in text area
- Manual grading by invigilator

### 3. **Programming/Code Questions**
- Added new question type: `code`
- Added `programming_language` field to Question model
- Supported languages: Python, Java, C++, JavaScript, C
- Code editor features:
  - Dark theme code textarea with monospace font
  - Syntax highlighting styling
  - Auto-save functionality
  - Language badge display
  - Larger text area (200px height)
- Manual grading by invigilator
- Students can write code in browser or paste from local IDE

## Files Modified

1. **database.py**
   - Added `programming_language` column to Question model
   - Added `allow_calculator` column to Question model
   - Updated question_type to support 'code' type

2. **config.py**
   - Added CALCULATOR_WHITELIST for math questions

3. **app.py**
   - Updated manage_questions route to handle code questions
   - Added programming_language and allow_calculator handling

4. **templates/manage_questions.html**
   - Added "Programming/Code" option to question type dropdown
   - Added programming language selector (shows for code questions)
   - Added calculator permission checkbox
   - Updated JavaScript to toggle code options

5. **templates/exam.html**
   - Added code editor section with dark theme
   - Added language badge display
   - Added calculator allowed badge
   - Monospace font for code textarea

6. **EXAM_INSTRUCTIONS.md**
   - Created student instructions document

## How to Use

### For Invigilators:
1. Go to Exam Schedule → Manage Questions
2. Select question type:
   - **Essay/Short Answer**: Regular text questions
   - **Multiple Choice**: MCQ with 4 options
   - **Programming/Code**: Code questions
3. For code questions, select programming language
4. Check "Allow calculator" for math questions
5. Add question and assign points

### For Students:
1. Math questions with calculator badge allow system calculator use
2. Code questions show dark code editor with language indicator
3. Write code directly or paste from local IDE
4. All answers auto-save

## Database Migration
- Run `db.create_all()` to add new columns (already done)
- Existing questions remain unchanged
- New fields default to NULL/False

## Security Notes
- Calculator apps in whitelist won't trigger tab switch alerts
- Copy-paste still blocked for non-code questions
- Code questions allow paste functionality
- All other security measures remain active

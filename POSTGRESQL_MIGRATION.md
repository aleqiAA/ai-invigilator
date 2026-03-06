# PostgreSQL Migration Guide

## Step 1: Install PostgreSQL

### Windows:
1. Download from https://www.postgresql.org/download/windows/
2. Run installer (default port 5432)
3. Remember the password you set for 'postgres' user

### macOS:
```bash
brew install postgresql
brew services start postgresql
```

### Linux:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## Step 2: Install Python PostgreSQL Driver

```bash
pip install psycopg2-binary
```

## Step 3: Create Database

### Windows (Command Prompt):
```cmd
psql -U postgres
CREATE DATABASE ai_invigilator;
\q
```

### macOS/Linux:
```bash
sudo -u postgres psql
CREATE DATABASE ai_invigilator;
\q
```

## Step 4: Update .env File

Change this line in `.env`:
```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ai_invigilator
```

Replace `your_password` with your PostgreSQL password.

## Step 5: Migrate Data (Optional)

If you have existing SQLite data to migrate:

```python
# migrate_to_postgres.py
from app import app, db
from database import *
import os

# Backup current SQLite data
os.system('copy ai_invigilator.db ai_invigilator.db.backup')

# Export data from SQLite
with app.app_context():
    # Get all data
    admins = Admin.query.all()
    invigilators = Invigilator.query.all()
    students = Student.query.all()
    sessions = ExamSession.query.all()
    questions = Question.query.all()
    answers = Answer.query.all()
    alerts = Alert.query.all()
    activities = ActivityLog.query.all()

# Switch to PostgreSQL in .env
# DATABASE_URL=postgresql://...

# Import data to PostgreSQL
with app.app_context():
    db.create_all()
    
    for admin in admins:
        db.session.add(admin)
    for inv in invigilators:
        db.session.add(inv)
    for student in students:
        db.session.add(student)
    # ... add all other records
    
    db.session.commit()
    print("Migration complete!")
```

## Step 6: Test Connection

Run the app and visit: http://localhost:5000/health

You should see:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00",
  "database": "connected"
}
```

## Step 7: Update Production Config

For production deployment, use environment variable:

```bash
# Railway, Render, Heroku automatically provide DATABASE_URL
# Just ensure psycopg2-binary is in requirements.txt
```

## Troubleshooting

### Error: "psycopg2.OperationalError: FATAL: password authentication failed"
- Check your password in DATABASE_URL
- Ensure PostgreSQL is running: `pg_ctl status`

### Error: "could not connect to server"
- Start PostgreSQL service
- Windows: Services → PostgreSQL → Start
- macOS: `brew services start postgresql`
- Linux: `sudo systemctl start postgresql`

### Error: "database does not exist"
- Create the database: `psql -U postgres -c "CREATE DATABASE ai_invigilator;"`

## Performance Benefits

SQLite → PostgreSQL improvements:
- ✅ Handles 100+ concurrent users
- ✅ No database locking issues
- ✅ Better crash recovery
- ✅ Full ACID compliance
- ✅ Production-ready backups
- ✅ Supports connection pooling

## Backup PostgreSQL

### Manual backup:
```bash
pg_dump -U postgres ai_invigilator > backup.sql
```

### Restore from backup:
```bash
psql -U postgres ai_invigilator < backup.sql
```

### Automated daily backups (Windows Task Scheduler):
Create `backup.bat`:
```batch
@echo off
set PGPASSWORD=your_password
pg_dump -U postgres ai_invigilator > backups\backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.sql
```

Schedule to run daily at 2 AM.

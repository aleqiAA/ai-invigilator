# PostgreSQL Setup - Complete Guide

## Step 1: Install PostgreSQL

**Windows:**
1. Download from https://www.postgresql.org/download/windows/
2. Run installer (keep default port 5432)
3. Set password for 'postgres' user (remember this!)

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## Step 2: Install Python Driver

```bash
pip install psycopg2-binary
```

## Step 3: Create Database

**Windows (Command Prompt):**
```cmd
psql -U postgres
# Enter password when prompted
CREATE DATABASE ai_invigilator;
\q
```

**macOS/Linux:**
```bash
sudo -u postgres psql
CREATE DATABASE ai_invigilator;
\q
```

## Step 4: Update .env File

Edit your `.env` file and change the DATABASE_URL line:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/ai_invigilator
```

Replace `YOUR_PASSWORD` with the password you set in Step 1.

## Step 5: Migrate Your Data

Run the migration script:

```bash
python migrate_to_postgres.py
```

You should see:
```
Found SQLite database at: ai_invigilator.db
✓ Tables created in PostgreSQL
✓ Migrated X admins
✓ Migrated X invigilators
✓ Migrated X students
✓ Migrated X exam sessions
✓ Migrated X alerts
✓ Migrated X questions
✓ Migrated X answers
✓ Migrated X activity logs

✅ Migration complete! Your data is now in PostgreSQL.
```

## Step 6: Test the Connection

Start your app:
```bash
python app.py
```

Visit: http://localhost:5000/health

You should see:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00",
  "database": "connected"
}
```

## Step 7: Backup Your SQLite File

Once everything works:
```bash
# Windows
move ai_invigilator.db ai_invigilator.db.backup

# macOS/Linux
mv ai_invigilator.db ai_invigilator.db.backup
```

## Troubleshooting

### "psycopg2.OperationalError: FATAL: password authentication failed"
- Check your password in DATABASE_URL
- Ensure PostgreSQL is running

### "could not connect to server"
- Start PostgreSQL:
  - Windows: Services → PostgreSQL → Start
  - macOS: `brew services start postgresql`
  - Linux: `sudo systemctl start postgresql`

### "database does not exist"
- Create it: `psql -U postgres -c "CREATE DATABASE ai_invigilator;"`

### Migration script shows "No SQLite database found"
- This is OK if starting fresh
- Tables will be created empty in PostgreSQL

## Daily Backup (Recommended)

Create `backup.bat` (Windows) or `backup.sh` (macOS/Linux):

**Windows:**
```batch
@echo off
set PGPASSWORD=YOUR_PASSWORD
pg_dump -U postgres ai_invigilator > backups\backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.sql
```

**macOS/Linux:**
```bash
#!/bin/bash
export PGPASSWORD=YOUR_PASSWORD
pg_dump -U postgres ai_invigilator > backups/backup_$(date +%Y%m%d).sql
```

Schedule to run daily at 2 AM using Task Scheduler (Windows) or cron (macOS/Linux).

## Production Deployment

For production (Railway, Render, Heroku):
- They provide DATABASE_URL automatically
- Just ensure `psycopg2-binary` is in requirements.txt
- No manual setup needed

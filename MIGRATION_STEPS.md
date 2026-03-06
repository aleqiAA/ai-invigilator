# PostgreSQL Migration - Step by Step

## Step 1: Install PostgreSQL

### Option A: Using Winget (Recommended)
Open Command Prompt or PowerShell and run:
```
winget install PostgreSQL.PostgreSQL.16
```

### Option B: Manual Download
1. Go to: https://www.postgresql.org/download/windows/
2. Download PostgreSQL 16 installer
3. Run installer
4. IMPORTANT: Write down the password you set for 'postgres' user
5. Keep default port: 5432
6. Complete installation

## Step 2: Verify PostgreSQL is Running

After installation, check if service is running:
```
sc query postgresql-x64-16
```

Should show: STATE: RUNNING

If not running, start it:
```
net start postgresql-x64-16
```

## Step 3: Create Database

Run this Python script:
```
python create_postgres_db.py
```

## Step 4: Update .env File

Replace YOUR_PASSWORD_HERE with the actual password you set during installation:
```
DATABASE_URL=postgresql://postgres:YOUR_ACTUAL_PASSWORD@localhost:5432/ai_invigilator
```

## Step 5: Migrate Data

Run migration script:
```
python migrate_to_postgres.py
```

## Step 6: Verify Migration

Run verification:
```
python verify_database.py
```

## Step 7: Test Application

Start your Flask app and test login with:
- Email: admin@aiinvigilator.com
- Password: admin123

---

## Current Status: Step 1 - Install PostgreSQL

Tell me when PostgreSQL installation is complete and what password you set.

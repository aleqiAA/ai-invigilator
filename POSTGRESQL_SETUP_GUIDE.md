# PostgreSQL Setup Guide for AI Invigilator

This guide covers setting up PostgreSQL for production deployment while keeping SQLite for local development.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local PostgreSQL Setup (Optional)](#local-postgresql-setup-optional)
3. [Production Deployment](#production-deployment)
4. [Database Migrations](#database-migrations)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### For Local Development (SQLite - Default)

No changes needed! Just run:

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Your app will use SQLite automatically.

### For Production (PostgreSQL)

1. Get a PostgreSQL database URL from Railway, Render, or your provider
2. Set the `DATABASE_URL` environment variable
3. Run migrations: `flask db upgrade`

---

## Local PostgreSQL Setup (Optional)

If you want to test PostgreSQL locally before deploying:

### Step 1: Install PostgreSQL

**Windows:**
- Download: https://www.postgresql.org/download/windows/
- Or use PostgreSQL via Docker: `docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres`

**Mac:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Step 2: Create Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE ai_invigilator;
CREATE USER ai_invigilator_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ai_invigilator TO ai_invigilator_user;
\q
```

### Step 3: Update .env File

```env
FLASK_ENV=development
DATABASE_URL=postgresql://ai_invigilator_user:your_password@localhost:5432/ai_invigilator
```

### Step 4: Install PostgreSQL Adapter

```bash
pip install psycopg2-binary
```

### Step 5: Run Migrations

```bash
flask db upgrade
```

---

## Production Deployment

### Railway.app

1. **Create a new project** on [Railway](https://railway.app)
2. **Add PostgreSQL database:**
   - Click "New" → "Database" → "PostgreSQL"
   - Copy the `DATABASE_URL` from the Variables tab
3. **Deploy your app:**
   - Push code to GitHub
   - Connect Railway to your GitHub repo
   - Railway will auto-detect Python/Flask
4. **Set environment variables:**
   ```
   FLASK_ENV=production
   DATABASE_URL=<from Railway PostgreSQL>
   SECRET_KEY=<generate secure key>
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   AFRICASTALKING_API_KEY=your-api-key
   ```
5. **Run migrations:**
   - In Railway dashboard, go to your PostgreSQL service
   - Click "Open in Browser" or use Railway CLI:
   ```bash
   railway run flask db upgrade
   ```

### Render.com

1. **Create a new Web Service** on [Render](https://render.com)
2. **Connect your GitHub repository**
3. **Add PostgreSQL:**
   - Click "New" → "PostgreSQL"
   - Copy the internal database URL
4. **Environment variables:**
   ```
   FLASK_ENV=production
   DATABASE_URL=<from Render PostgreSQL>
   SECRET_KEY=<generate secure key>
   ```
5. **Build Command:** `pip install -r requirements.txt`
6. **Start Command:** `gunicorn app:app`
7. **Run migrations** (in Render dashboard → Shell):
   ```bash
   flask db upgrade
   ```

### Heroku

1. **Install Heroku CLI**
2. **Create app:**
   ```bash
   heroku create your-app-name
   ```
3. **Add PostgreSQL:**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```
4. **Set environment variables:**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   heroku config:set MAIL_USERNAME=your-email@gmail.com
   heroku config:set MAIL_PASSWORD=your-app-password
   ```
5. **Deploy:**
   ```bash
   git push heroku main
   heroku run flask db upgrade
   ```

---

## Database Migrations

### After Model Changes

Whenever you modify `database.py`:

```bash
# Create migration file
flask db migrate -m "describe your change"

# Apply migration
flask db upgrade
```

### Rollback Migration

```bash
# Rollback one migration
flask db downgrade -1

# Rollback to specific revision
flask db downgrade <revision_id>
```

### Check Migration Status

```bash
# Show current version
flask db current

# Show all migrations
flask db history
```

---

## Environment Variables

### Required for Production

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` |
| `SECRET_KEY` | Session encryption key | `a1b2c3d4...` (32+ chars) |

### Recommended for Production

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_POOL_SIZE` | Database connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Max extra connections | `20` |
| `MAIL_USERNAME` | Email for notifications | - |
| `MAIL_PASSWORD` | Email app password | - |
| `AFRICASTALKING_API_KEY` | SMS service API key | - |

### Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate SECURITY_PASSWORD_SALT
python -c "import secrets; print(secrets.token_hex(16))"
```

---

## Troubleshooting

### Error: psycopg2 not found

```bash
pip install psycopg2-binary
```

For production, use `psycopg2` instead:
```bash
pip uninstall psycopg2-binary
pip install psycopg2
```

### Error: DATABASE_URL not set

Check your environment variables:
```bash
# Linux/Mac
echo $DATABASE_URL

# Windows
echo %DATABASE_URL%

# In Python
python -c "import os; print(os.environ.get('DATABASE_URL'))"
```

### Error: Connection refused

1. Check PostgreSQL is running: `pg_isready` or `service postgresql status`
2. Verify host/port in DATABASE_URL
3. Check firewall settings

### Error: Migration fails

1. Check current version: `flask db current`
2. Review migration files in `migrations/versions/`
3. Try: `flask db stamp head` (marks DB as up-to-date)

### SQLite to PostgreSQL Migration

If you have existing SQLite data:

```bash
# Install pgloader
# Ubuntu: sudo apt install pgloader
# Mac: brew install pgloader

# Migrate SQLite to PostgreSQL
pgloader sqlite:///ai_invigilator.db postgresql://user:pass@host:port/db
```

---

## Configuration Comparison

| Setting | Development (SQLite) | Production (PostgreSQL) |
|---------|---------------------|------------------------|
| Database | `sqlite:///ai_invigilator.db` | `postgresql://...` |
| Pool Size | N/A | 10 |
| Max Overflow | N/A | 20 |
| Session Cookie | HTTP OK | HTTPS Only |
| Debug Mode | On | Off |
| Rate Limiting | Memory | Redis (recommended) |

---

## Support

For issues:
1. Check logs: `logs/ai_invigilator.log`
2. Enable debug logging: `LOG_LEVEL=DEBUG`
3. Review Flask-Migrate docs: https://flask-migrate.readthedocs.io/

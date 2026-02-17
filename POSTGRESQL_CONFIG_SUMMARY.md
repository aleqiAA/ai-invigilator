# PostgreSQL Configuration Summary

## Files Changed

### 1. config.py
- Added python-dotenv loading
- Added PostgreSQL connection pool settings
- Created separate DevelopmentConfig and ProductionConfig classes
- Added environment-based configuration selection

### 2. requirements.txt
- Added: `psycopg2-binary==2.9.9` (PostgreSQL adapter)

### 3. .env.example
- Comprehensive documentation of all environment variables
- DATABASE_URL examples for different providers
- Pool configuration settings
- Email and SMS configuration

### 4. .gitignore
- Added: `.env.production`, `.env.*.local`
- Added common Python/Testing ignore patterns

### 5. app.py
- Updated imports to use `get_config()`
- Added SQLite-specific conditional logic
- Added configuration initialization logging

### 6. POSTGRESQL_SETUP_GUIDE.md (NEW)
- Complete setup instructions
- Local PostgreSQL setup
- Railway/Render/Heroku deployment guides
- Migration commands
- Troubleshooting

---

## Quick Setup Commands

### Install Dependencies
```bash
cd "c:\Users\alexn\OneDrive\python file schol\ai_invigilator"
.venv\Scripts\activate
pip install -r requirements.txt
```

### For Local Development (SQLite - No changes needed)
```bash
# Just run the app
python app.py
```

### For Production (PostgreSQL)

1. **Set DATABASE_URL in .env:**
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-generated-secret-key
```

2. **Run migrations:**
```bash
flask db upgrade
```

3. **Start the app:**
```bash
# Development
python app.py

# Production (with gunicorn)
pip install gunicorn
gunicorn app:app
```

---

## Environment Variables Reference

### Development (.env)
```env
FLASK_ENV=development
DATABASE_URL=sqlite:///ai_invigilator.db
SECRET_KEY=dev-secret-key-change-in-production
```

### Production (.env.production or platform variables)
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=<64-char-hex-string>
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
AFRICASTALKING_API_KEY=your-api-key
```

---

## Generate Secure Keys

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Example output: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`

---

## Deployment Platform DATABASE_URL Examples

### Railway
```
postgresql://postgres:password@railway.app:5432/railway
```

### Render
```
postgresql://user:password@host.db.render.com:5432/db-name
```

### Heroku
```
postgresql://user:password@host.ec2.amazonaws.com:5432/db-name
```

### Local PostgreSQL
```
postgresql://postgres:password@localhost:5432/ai_invigilator
```

---

## Migration Commands

```bash
# After model changes
flask db migrate -m "description of change"
flask db upgrade

# Check status
flask db current
flask db history

# Rollback
flask db downgrade -1
```

---

## Testing the Configuration

### Check which database is being used
```python
# In Python shell
from app import app
print(app.config['SQLALCHEMY_DATABASE_URI'])
```

### Verify environment
```python
import os
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print(f"DATABASE_URL set: {bool(os.environ.get('DATABASE_URL'))}")
```

---

## Next Steps

1. **For local development:** Nothing to do! SQLite works out of the box.

2. **For production deployment:**
   - Choose a platform (Railway, Render, Heroku)
   - Create PostgreSQL database
   - Copy DATABASE_URL to environment variables
   - Set SECRET_KEY and other required vars
   - Run `flask db upgrade`
   - Deploy!

3. **Optional - Test PostgreSQL locally:**
   - Install PostgreSQL
   - Create database
   - Set DATABASE_URL in .env
   - Run migrations

---

## Support

See `POSTGRESQL_SETUP_GUIDE.md` for detailed instructions.

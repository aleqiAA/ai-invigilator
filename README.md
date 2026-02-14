# AI Invigilator System

Automated exam monitoring and proctoring solution for Open University of Kenya (OUK).

## Features

- 🎥 Real-time camera monitoring
- 👥 Bulk student import (CSV/Excel)
- 📅 Exam scheduling with cohorts
- ⚠️ Automated alert system
- 📝 Question management (Essay & Multiple Choice)
- 📊 Integrity scoring & PDF reports
- 📱 Mobile responsive design
- 🔒 Secure authentication & session management

## Installation

```bash
# Clone repository
cd ai_invigilator

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

## Configuration

Edit `config.py`:
- `SECRET_KEY`: Auto-generated (keep secure)
- `SQLALCHEMY_DATABASE_URI`: Database connection
- Email settings for notifications

## Security Features

✅ Password hashing (Werkzeug)  
✅ Rate limiting (Flask-Limiter)  
✅ Session timeouts (1 hour)  
✅ Role-based access control  
✅ CSRF protection  
✅ Input validation  

## Database

**Current**: SQLite (development)  
**Production**: PostgreSQL recommended

To reset database:
```bash
del instance\invigilator.db
python app.py
```

## Usage

### Invigilator
1. Register at `/invigilator/register`
2. Login and bulk import students
3. Schedule exams by cohort
4. Monitor live sessions
5. View reports and alerts

### Student
1. Login with email + Student ID (password)
2. View scheduled exams
3. Take exams with camera monitoring
4. Submit answers (auto-saved)

## API Endpoints

See `LMS_INTEGRATION.md` for REST API documentation.

## Error Handling

All critical routes have try-except blocks:
- Database operations wrapped in transactions
- File uploads validated
- Camera errors reported to invigilator
- User-friendly error messages

## Testing

```bash
# Run tests (when implemented)
pytest tests/
```

## Deployment

### Local Network
```bash
python app.py
# Access from other devices: http://YOUR_IP:5000
```

### Production
1. Set `debug=False` in app.py
2. Use production WSGI server (Gunicorn)
3. Configure PostgreSQL
4. Set up HTTPS
5. Configure firewall

## Support

For issues or questions, contact the development team.

## License

Proprietary - Open University of Kenya

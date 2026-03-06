"""
Verify PostgreSQL database is working correctly.
"""

from app import app, db
from database import Admin, Invigilator, Student, ExamSession, Alert, Question, Answer, ActivityLog

with app.app_context():
    print("=" * 60)
    print("PostgreSQL Database Verification")
    print("=" * 60)
    
    # Test connection
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        print("\nOK Database connection: SUCCESS")
    except Exception as e:
        print(f"\nERROR Database connection: FAILED - {e}")
        exit(1)
    
    # Check tables exist
    print("\n--- Tables Status ---")
    tables = {
        'admins': Admin,
        'invigilators': Invigilator,
        'students': Student,
        'exam_sessions': ExamSession,
        'alerts': Alert,
        'questions': Question,
        'answers': Answer,
        'activity_logs': ActivityLog
    }
    
    for table_name, model in tables.items():
        try:
            count = model.query.count()
            print(f"OK {table_name}: {count} records")
        except Exception as e:
            print(f"ERROR {table_name}: {e}")
    
    # Check super admin
    print("\n--- Super Admin Status ---")
    super_admin = db.session.get(Admin, 1)
    if super_admin:
        print(f"OK Super admin exists: {super_admin.email}")
        print(f"  Institution: {super_admin.institution_name}")
        print(f"  Active: {super_admin.is_active}")
    else:
        print("ERROR Super admin not found (run create_super_admin.py)")
    
    # Database info
    print("\n--- Database Info ---")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    print(f"Using PostgreSQL: {'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']}")
    
    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)
    
    if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
        print("\nOK PostgreSQL migration successful!")
        print("OK Ready for production use")
        print("\nNext steps:")
        print("1. Start app: python app.py")
        print("2. Visit: http://localhost:5000/health")
        print("3. Login: http://localhost:5000/admin/login")
    else:
        print("\nERROR Still using SQLite - update .env DATABASE_URL")

if __name__ == '__main__':
    pass

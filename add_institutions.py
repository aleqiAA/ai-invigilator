from app import app, db
from database import Institution, Admin, Invigilator, Student, ExamSession
from sqlalchemy import text

print("Multi-Tenant Institution Migration")
print("=" * 50)

with app.app_context():
    # Step 1: Create institutions table
    print("\n1. Creating institutions table...")
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS institutions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL UNIQUE,
            plan VARCHAR(50) DEFAULT 'free',
            session_limit INTEGER DEFAULT 100,
            sessions_used_this_month INTEGER DEFAULT 0,
            billing_email VARCHAR(120),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.session.commit()
    print("   OK Institutions table created")

    # Step 2: Add institution_id columns
    print("\n2. Adding institution_id columns...")
    
    tables = ['admins', 'invigilator', 'student', 'exam_session']
    for table in tables:
        try:
            db.session.execute(text(f"""
                ALTER TABLE {table} 
                ADD COLUMN IF NOT EXISTS institution_id INTEGER 
                REFERENCES institutions(id)
            """))
            db.session.commit()
            print(f"   OK Added institution_id to {table}")
        except Exception as e:
            db.session.rollback()
            print(f"   - {table} already has institution_id or error: {e}")

    # Step 3: Create default institution
    print("\n3. Creating default institution...")
    default_inst = Institution.query.filter_by(name='Default Institution').first()
    if not default_inst:
        default_inst = Institution(
            name='Default Institution',
            plan='pro',
            session_limit=10000,
            billing_email='admin@aiinvigilator.com'
        )
        db.session.add(default_inst)
        db.session.commit()
        print(f"   OK Created default institution (ID: {default_inst.id})")
    else:
        print(f"   - Default institution already exists (ID: {default_inst.id})")

    # Step 4: Link existing data to default institution
    print("\n4. Linking existing data to default institution...")
    
    admins_updated = Admin.query.filter_by(institution_id=None).update({'institution_id': default_inst.id})
    invigilators_updated = Invigilator.query.filter_by(institution_id=None).update({'institution_id': default_inst.id})
    students_updated = Student.query.filter_by(institution_id=None).update({'institution_id': default_inst.id})
    sessions_updated = ExamSession.query.filter_by(institution_id=None).update({'institution_id': default_inst.id})
    
    db.session.commit()
    
    print(f"   OK Linked {admins_updated} admins")
    print(f"   OK Linked {invigilators_updated} invigilators")
    print(f"   OK Linked {students_updated} students")
    print(f"   OK Linked {sessions_updated} exam sessions")

    # Step 5: Create institutions from existing admins
    print("\n5. Creating institutions from admin institution_name...")
    
    admins = Admin.query.all()
    created_count = 0
    
    for admin in admins:
        if admin.institution_name and admin.institution_name != 'Default Institution':
            existing = Institution.query.filter_by(name=admin.institution_name).first()
            if not existing:
                new_inst = Institution(
                    name=admin.institution_name,
                    plan='free',
                    session_limit=100,
                    billing_email=admin.email
                )
                db.session.add(new_inst)
                db.session.flush()
                
                admin.institution_id = new_inst.id
                
                # Link admin's invigilators
                for inv in admin.invigilators:
                    inv.institution_id = new_inst.id
                
                created_count += 1
            else:
                admin.institution_id = existing.id
                for inv in admin.invigilators:
                    inv.institution_id = existing.id
    
    db.session.commit()
    print(f"   OK Created {created_count} new institutions from admin data")

    # Step 6: Summary
    print("\n" + "=" * 50)
    print("Migration Complete!")
    print("=" * 50)
    print(f"Total Institutions: {Institution.query.count()}")
    print(f"Total Admins: {Admin.query.count()}")
    print(f"Total Invigilators: {Invigilator.query.count()}")
    print(f"Total Students: {Student.query.count()}")
    print(f"Total Exam Sessions: {ExamSession.query.count()}")
    print("\nAll data is now multi-tenant ready!")

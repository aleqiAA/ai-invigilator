#!/usr/bin/env python
"""
Debug script to check login issues
Run: python debug_login.py
"""
import sys
from app import app
from database import db, Invigilator, Admin, Institution

def debug():
    print("=" * 60)
    print("LOGIN DEBUG SCRIPT")
    print("=" * 60)
    
    with app.app_context():
        # 1. Check database connection
        print("\n1. Database Connection:")
        try:
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1'))
            print("   [OK] Database connected")
        except Exception as e:
            print(f"   [ERROR] Database error: {e}")
            print("   -> Check if PostgreSQL is running or switch to SQLite")
            return
        
        # 2. Check database URI
        print("\n2. Database URI:")
        uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')
        masked = uri[:20] + '...' if len(uri) > 20 else uri
        print(f"   {masked}")
        
        # 3. Check institutions
        print("\n3. Institutions:")
        try:
            inst_count = Institution.query.count()
            print(f"   Count: {inst_count}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 4. Check admins
        print("\n4. Admins:")
        try:
            admin_count = Admin.query.count()
            print(f"   Count: {admin_count}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # 5. Check invigilators
        print("\n5. Invigilators:")
        try:
            invigilators = Invigilator.query.all()
            print(f"   Count: {len(invigilators)}")
            for inv in invigilators:
                print(f"   - ID={inv.id}, Name={inv.name}, Email={inv.email}, Active={inv.is_active}")
            
            if len(invigilators) == 0:
                print("\n   [WARNING] NO INVIGILATORS FOUND!")
                print("   Creating test invigilator...")
                
                # Create test institution if needed
                inst = Institution.query.first()
                if not inst:
                    inst = Institution(name='Test Institution', plan='free')
                    db.session.add(inst)
                    db.session.commit()
                    print(f"   Created institution: {inst.name}")
                
                # Create test admin if needed
                admin = Admin.query.first()
                if not admin:
                    admin = Admin(name='Test Admin', email='admin@test.com', institution_name='Test Institution')
                    admin.set_password('admin123')
                    admin.institution_id = inst.id
                    db.session.add(admin)
                    db.session.commit()
                    print(f"   Created admin: {admin.email} (password: admin123)")
                
                # Create test invigilator
                test_inv = Invigilator(
                    name='Test Invigilator',
                    email='invigilator@test.com',
                    institution_id=inst.id,
                    is_active=True
                )
                test_inv.set_password('password123')
                db.session.add(test_inv)
                db.session.commit()
                print(f"   [OK] Created test invigilator:")
                print(f"      Email: invigilator@test.com")
                print(f"      Password: password123")
                
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("DEBUG COMPLETE")
        print("=" * 60)

if __name__ == '__main__':
    debug()

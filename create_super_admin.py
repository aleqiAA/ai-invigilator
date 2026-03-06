"""
Create super admin account (ID=1).
This is the first admin who can approve other institutions.
"""

from app import app, db
from database import Admin

with app.app_context():
    # Check if super admin exists
    super_admin = Admin.query.get(1)
    
    if super_admin:
        print("Super admin already exists!")
        print(f"Email: {super_admin.email}")
    else:
        # Create super admin
        admin = Admin(
            name="Super Admin",
            email="admin@aiinvigilator.com",
            institution_name="AI Invigilator Platform",
            is_active=True
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        
        print("Super admin created successfully!")
        print("Email: admin@aiinvigilator.com")
        print("Password: admin123")
        print("\nLogin at: http://localhost:5000/admin/login")
        print("\nCHANGE THIS PASSWORD IMMEDIATELY!")

if __name__ == '__main__':
    pass

"""
Run this once to fix the database:
    python fix_database.py
"""
from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        # Add missing columns to invigilator table
        try:
            conn.execute(db.text("ALTER TABLE invigilator ADD COLUMN admin_id INTEGER"))
            print("✓ Added admin_id column")
        except Exception as e:
            print(f"  admin_id already exists (skipping): {e}")

        try:
            conn.execute(db.text("ALTER TABLE invigilator ADD COLUMN assigned_cohorts TEXT"))
            print("✓ Added assigned_cohorts column")
        except Exception as e:
            print(f"  assigned_cohorts already exists (skipping): {e}")

        # Create admins table if it doesn't exist
        try:
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    institution_name VARCHAR(200),
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME
                )
            """))
            print("✓ Created admins table")
        except Exception as e:
            print(f"  admins table already exists (skipping): {e}")

        conn.commit()

    print("\nDatabase fixed! You can now log in.")
    print("\nTo create your first admin account, run:")
    print("    python create_admin.py")
    
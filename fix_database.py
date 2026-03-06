"""
Run this to fix all missing columns:
    python fix_database.py
"""
from app import app, db

columns_to_add = [
    ("invigilator", "admin_id",           "INTEGER"),
    ("invigilator", "assigned_cohorts",   "TEXT"),
    ("invigilator", "is_active",          "BOOLEAN DEFAULT 1"),
    ("invigilator", "reset_token",        "VARCHAR(100)"),
    ("invigilator", "reset_token_expiry", "DATETIME"),
    ("invigilator", "created_at",         "DATETIME"),
]

with app.app_context():
    with db.engine.connect() as conn:

        # Add all missing columns to invigilator table
        for table, column, col_type in columns_to_add:
            try:
                conn.execute(db.text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                print(f"✓ Added {table}.{column}")
            except Exception:
                print(f"  {table}.{column} already exists (skipping)")

        # Create admins table
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
            print("✓ admins table ready")
        except Exception:
            print("  admins table already exists (skipping)")

        conn.commit()

    print("\n✅ Database fixed! Now run: python create_admin.py")
"""
Migration script to add is_auto_submitted column to exam_session table
"""
import sqlite3
from pathlib import Path

# Find the database file
db_path = Path(__file__).parent / 'instance' / 'invigilator.db'

# If not in instance folder, check root
if not db_path.exists():
    db_path = Path(__file__).parent / 'invigilator.db'

if not db_path.exists():
    print("Database not found at " + str(db_path))
    print("Please run the application first to create the database.")
    exit(1)

print("Using database: " + str(db_path))

# Connect to database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(exam_session)")
columns = [col[1] for col in cursor.fetchall()]

if 'is_auto_submitted' in columns:
    print("[OK] Column 'is_auto_submitted' already exists!")
else:
    print("Adding 'is_auto_submitted' column to exam_session table...")
    
    # Add the column
    cursor.execute('''
        ALTER TABLE exam_session 
        ADD COLUMN is_auto_submitted BOOLEAN DEFAULT 0
    ''')
    
    conn.commit()
    print("[OK] Column 'is_auto_submitted' added successfully!")

# Verify
cursor.execute("PRAGMA table_info(exam_session)")
columns = [col[1] for col in cursor.fetchall()]
print("\nCurrent exam_session columns: " + ", ".join(columns))

conn.close()
print("\nMigration completed successfully!")

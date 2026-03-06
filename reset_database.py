"""
Reset PostgreSQL database to clean slate.
Run this to start fresh with empty tables.
"""

from app import app, db

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Creating fresh tables...")
    db.create_all()
    print("\nDatabase reset complete! All tables are now empty.")

if __name__ == '__main__':
    pass

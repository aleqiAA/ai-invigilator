#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add reference_image column to Question table
Run this once to update existing database
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app import app
from database import db

print("=" * 70)
print("DATABASE MIGRATION - Add reference_image column")
print("=" * 70)

with app.app_context():
    try:
        # Check if column already exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('question')]
        
        if 'reference_image' in columns:
            print("\n✓ Column 'reference_image' already exists!")
        else:
            print("\nAdding 'reference_image' column to question table...")
            
            # Add the column
            with db.engine.connect() as conn:
                conn.execute(db.text('''
                    ALTER TABLE question 
                    ADD COLUMN reference_image TEXT
                '''))
                conn.commit()
            
            print("✓ Column added successfully!")
        
        print("\nMigration complete!")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("=" * 70)

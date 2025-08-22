#!/usr/bin/env python3
"""
Migration script to add title and description fields to Media table
"""
import sqlite3
import sys
from pathlib import Path

def migrate_media_table():
    db_path = Path("blog.db")
    
    if not db_path.exists():
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(media)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add title column if it doesn't exist
        if 'title' not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN title VARCHAR(200)")
            print("Added 'title' column to media table")
        else:
            print("'title' column already exists")
        
        # Add description column if it doesn't exist
        if 'description' not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN description TEXT")
            print("Added 'description' column to media table")
        else:
            print("'description' column already exists")
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_media_table()
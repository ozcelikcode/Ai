#!/usr/bin/env python3
"""
Migration script to add session_duration field to User table
"""
import sqlite3
import sys
from pathlib import Path

def migrate_user_table():
    db_path = Path("blog.db")
    
    if not db_path.exists():
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add session_duration column if it doesn't exist
        if 'session_duration' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN session_duration INTEGER DEFAULT 1440")
            print("Added 'session_duration' column to users table")
        else:
            print("'session_duration' column already exists")
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_user_table()
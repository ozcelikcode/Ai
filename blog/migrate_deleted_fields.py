#!/usr/bin/env python3
"""
Migration script to add deleted and draft fields to existing database
"""

import sqlite3
from datetime import datetime
import os

def migrate_database():
    """Add new fields to existing database tables"""
    db_path = "blog.db"
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting database migration...")
        
        # Check current schema
        cursor.execute("PRAGMA table_info(posts)")
        posts_columns = [column[1] for column in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(pages)")
        pages_columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing fields to posts table
        if 'is_deleted' not in posts_columns:
            print("Adding is_deleted to posts table...")
            cursor.execute("ALTER TABLE posts ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
        
        if 'deleted_at' not in posts_columns:
            print("Adding deleted_at to posts table...")
            cursor.execute("ALTER TABLE posts ADD COLUMN deleted_at DATETIME")
        
        # Add missing fields to pages table
        if 'is_deleted' not in pages_columns:
            print("Adding is_deleted to pages table...")
            cursor.execute("ALTER TABLE pages ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
        
        if 'deleted_at' not in pages_columns:
            print("Adding deleted_at to pages table...")
            cursor.execute("ALTER TABLE pages ADD COLUMN deleted_at DATETIME")
        
        if 'is_draft' not in pages_columns:
            print("Adding is_draft to pages table...")
            cursor.execute("ALTER TABLE pages ADD COLUMN is_draft BOOLEAN DEFAULT 1")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    
    except Exception as e:
        print(f"Migration error: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("Database migration completed successfully!")
    else:
        print("Database migration failed!")
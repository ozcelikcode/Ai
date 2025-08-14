#!/usr/bin/env python3
"""
Database migration script to add new columns to settings table.
Run this script to update your existing database with the new features.
"""

import sqlite3
import os

def migrate_database():
    """Add new columns to the settings table"""
    db_path = "blog.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        if not cursor.fetchone():
            print("Settings table does not exist. Creating it...")
            cursor.execute("""
                CREATE TABLE settings (
                    id INTEGER PRIMARY KEY,
                    site_title VARCHAR(200) DEFAULT 'My Blog',
                    site_logo VARCHAR(200),
                    logo_type VARCHAR(20) DEFAULT 'text',
                    logo_icon VARCHAR(100),
                    favicon VARCHAR(200),
                    meta_description VARCHAR(300),
                    meta_keywords VARCHAR(300),
                    footer_content TEXT,
                    comment_limit INTEGER DEFAULT 500,
                    ai_prompt TEXT DEFAULT 'Write a blog post about the given topic',
                    ai_content_length VARCHAR(50) DEFAULT 'medium',
                    ai_content_type VARCHAR(50) DEFAULT 'informative',
                    updated_at DATETIME
                )
            """)
            print("Settings table created successfully!")
        else:
            # Add new columns if they don't exist
            new_columns = [
                ("logo_type", "VARCHAR(20) DEFAULT 'text'"),
                ("logo_icon", "VARCHAR(100)"),
                ("footer_content", "TEXT"),
                ("comment_limit", "INTEGER DEFAULT 500")
            ]
            
            for column_name, column_def in new_columns:
                try:
                    cursor.execute(f"ALTER TABLE settings ADD COLUMN {column_name} {column_def}")
                    print(f"Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"Column {column_name} already exists, skipping...")
                    else:
                        print(f"Error adding column {column_name}: {e}")
        
        # Ensure there's at least one settings record
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO settings (site_title, comment_limit, logo_type) 
                VALUES ('AI Blog', 500, 'text')
            """)
            print("Created default settings record")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
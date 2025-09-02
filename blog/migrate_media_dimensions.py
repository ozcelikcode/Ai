"""
Migration script to add width and height fields to media table
"""

import sqlite3
import os
from pathlib import Path

def migrate_media_dimensions():
    """Add width and height columns to media table"""
    
    # Connect to database
    db_path = Path("blog.db")
    if not db_path.exists():
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(media)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add width column if it doesn't exist
        if 'width' not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN width INTEGER")
            print("Added 'width' column to media table")
        else:
            print("'width' column already exists")
            
        # Add height column if it doesn't exist  
        if 'height' not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN height INTEGER")
            print("Added 'height' column to media table")
        else:
            print("'height' column already exists")
        
        conn.commit()
        conn.close()
        
        print("Media dimensions migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_media_dimensions()
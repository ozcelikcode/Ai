"""
Migration script to add timezone field to settings table
"""

import sqlite3
import os
from pathlib import Path

def migrate_timezone():
    """Add timezone column to settings table"""
    
    # Connect to database
    db_path = Path("blog.db")
    if not db_path.exists():
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if timezone column already exists
        cursor.execute("PRAGMA table_info(settings)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add timezone column if it doesn't exist
        if 'timezone' not in columns:
            cursor.execute("ALTER TABLE settings ADD COLUMN timezone TEXT DEFAULT 'Europe/Istanbul'")
            print("Added 'timezone' column to settings table with default value 'Europe/Istanbul'")
        else:
            print("'timezone' column already exists")
            
        # Update any existing null timezone values to default
        cursor.execute("UPDATE settings SET timezone = 'Europe/Istanbul' WHERE timezone IS NULL OR timezone = ''")
        
        conn.commit()
        conn.close()
        
        print("Timezone migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_timezone()
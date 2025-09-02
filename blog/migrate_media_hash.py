"""
Migration script to add file_hash field and calculate hashes for existing media files
"""

import sqlite3
import os
from pathlib import Path
import hashlib

def calculate_file_hash(file_path):
    """Calculate SHA256 hash of existing file"""
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
            return hashlib.sha256(file_content).hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None

def migrate_media_hash():
    """Add file_hash column and calculate hashes for existing files"""
    
    # Connect to database
    db_path = Path("blog.db")
    if not db_path.exists():
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if file_hash column already exists
        cursor.execute("PRAGMA table_info(media)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add file_hash column if it doesn't exist
        if 'file_hash' not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN file_hash TEXT")
            print("Added 'file_hash' column to media table")
        else:
            print("'file_hash' column already exists")
        
        # Get all media records
        cursor.execute("SELECT id, file_path FROM media WHERE file_hash IS NULL OR file_hash = ''")
        media_records = cursor.fetchall()
        
        print(f"Processing {len(media_records)} media files...")
        
        updated_count = 0
        for media_id, file_path in media_records:
            file_hash = calculate_file_hash(file_path)
            
            if file_hash:
                cursor.execute("UPDATE media SET file_hash = ? WHERE id = ?", (file_hash, media_id))
                updated_count += 1
                print(f"  - Updated hash for media ID {media_id}")
            else:
                print(f"  - Could not calculate hash for media ID {media_id} (file: {file_path})")
        
        # Create index for better performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_hash ON media(file_hash)")
            print("Created index on file_hash column")
        except Exception as e:
            print(f"Index creation warning: {e}")
        
        # Create index for search optimization  
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_search ON media(title, original_name, description)")
            print("Created search optimization index")
        except Exception as e:
            print(f"Search index creation warning: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\nMigration completed successfully!")
        print(f"Updated {updated_count} out of {len(media_records)} media files with hashes")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_media_hash()
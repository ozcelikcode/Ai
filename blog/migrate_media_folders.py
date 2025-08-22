#!/usr/bin/env python3
"""
Migration script to add media folders table and folder_id to media table
"""
import sqlite3
from pathlib import Path

def migrate_media_folders():
    db_path = Path("blog.db")
    
    if not db_path.exists():
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create media_folders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                color VARCHAR(7) DEFAULT '#944f37',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created 'media_folders' table")
        
        # Check if folder_id column exists in media table
        cursor.execute("PRAGMA table_info(media)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add folder_id column if it doesn't exist
        if 'folder_id' not in columns:
            cursor.execute("ALTER TABLE media ADD COLUMN folder_id INTEGER REFERENCES media_folders(id)")
            print("Added 'folder_id' column to media table")
        else:
            print("'folder_id' column already exists in media table")
        
        # Create some default folders
        cursor.execute("SELECT COUNT(*) FROM media_folders")
        folder_count = cursor.fetchone()[0]
        
        if folder_count == 0:
            default_folders = [
                ("Genel", "Genel medya dosyaları", "#944f37"),
                ("Blog Resimleri", "Blog yazıları için resimler", "#059669"),
                ("Avatarlar", "Kullanıcı avatar resimleri", "#dc2626"),
                ("Belgeler", "PDF ve dökümanlar", "#d97706"),
                ("Banner", "Site banner ve header resimleri", "#7c3aed")
            ]
            
            for name, desc, color in default_folders:
                cursor.execute("""
                    INSERT INTO media_folders (name, description, color) 
                    VALUES (?, ?, ?)
                """, (name, desc, color))
            
            print("Created default folders")
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_media_folders()
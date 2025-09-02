"""
Update existing media records with missing metadata (width, height, title)
"""

import sqlite3
import os
from pathlib import Path
from PIL import Image

def update_existing_media_metadata():
    """Update existing media records with missing metadata"""
    
    # Connect to database
    db_path = Path("blog.db")
    if not db_path.exists():
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all media records that need updating
        cursor.execute("""
            SELECT id, filename, original_name, file_path, mime_type, title, width, height
            FROM media 
            WHERE width IS NULL OR height IS NULL OR title IS NULL
        """)
        
        media_records = cursor.fetchall()
        updated_count = 0
        
        for record in media_records:
            media_id, filename, original_name, file_path, mime_type, title, width, height = record
            
            print(f"Processing: {filename}")
            
            # Update title if missing
            if not title:
                # Generate title from original filename
                auto_title = Path(original_name).stem.replace('-', ' ').replace('_', ' ').title()
                cursor.execute("UPDATE media SET title = ? WHERE id = ?", (auto_title, media_id))
                print(f"  - Added title: {auto_title}")
            
            # Update dimensions if missing and it's an image
            if mime_type and mime_type.startswith('image/') and (not width or not height):
                try:
                    if os.path.exists(file_path):
                        with Image.open(file_path) as img:
                            img_width, img_height = img.size
                            cursor.execute("UPDATE media SET width = ?, height = ? WHERE id = ?", 
                                        (img_width, img_height, media_id))
                            print(f"  - Added dimensions: {img_width}x{img_height}")
                    else:
                        print(f"  - File not found: {file_path}")
                except Exception as e:
                    print(f"  - Error processing image: {e}")
            
            updated_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\nUpdated {updated_count} media records with missing metadata!")
        return True
        
    except Exception as e:
        print(f"Update failed: {e}")
        return False

if __name__ == "__main__":
    update_existing_media_metadata()
#!/usr/bin/env python3
"""
Migration script to add is_default column to categories table and create default category
"""
import sqlite3
import os
from datetime import datetime

def migrate_categories():
    db_path = "blog.db"
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if is_default column already exists
        cursor.execute("PRAGMA table_info(categories)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_default' not in columns:
            print("Adding is_default column to categories table...")
            cursor.execute("ALTER TABLE categories ADD COLUMN is_default BOOLEAN DEFAULT 0")
            conn.commit()
            print("[OK] is_default column added successfully")
        else:
            print("[INFO] is_default column already exists")
        
        # Check if default category exists
        cursor.execute("SELECT * FROM categories WHERE is_default = 1")
        default_category = cursor.fetchone()
        
        if not default_category:
            # Check if "Genel" category already exists
            cursor.execute("SELECT * FROM categories WHERE name = 'Genel'")
            existing_general = cursor.fetchone()
            
            if existing_general:
                # Update existing "Genel" category to be default
                cursor.execute("UPDATE categories SET is_default = 1 WHERE name = 'Genel'")
                print("[OK] Set existing 'Genel' category as default")
            else:
                # Create new default category
                now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO categories (name, slug, description, is_default, created_at) 
                    VALUES (?, ?, ?, ?, ?)
                """, ("Genel", "genel", "Genel kategorisi - varsayılan kategori", 1, now))
                print("[OK] Created new default 'Genel' category")
            
            conn.commit()
        else:
            print("[INFO] Default category already exists")
        
        # Update posts without category to use default category
        cursor.execute("SELECT id FROM categories WHERE is_default = 1")
        default_category_id = cursor.fetchone()[0]
        
        cursor.execute("UPDATE posts SET category_id = ? WHERE category_id IS NULL", (default_category_id,))
        updated_posts = cursor.rowcount
        
        if updated_posts > 0:
            print(f"[OK] Updated {updated_posts} posts to use default category")
        
        conn.commit()
        conn.close()
        
        print("[SUCCESS] Category migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    migrate_categories()
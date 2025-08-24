#!/usr/bin/env python3
"""
Database migration script to add hero section columns to settings table.
Run this script to update your existing database with hero section customization features.
"""

import sqlite3
import os

def migrate_database():
    """Add hero section columns to the settings table"""
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
            print("Settings table does not exist. Please run the main migration script first.")
            return
        
        # Add new hero section columns if they don't exist
        hero_columns = [
            ("hero_enabled", "BOOLEAN DEFAULT 1"),
            ("hero_title", "VARCHAR(500) DEFAULT 'AI Destekli Blog Platformu'"),
            ("hero_subtitle", "TEXT DEFAULT 'Yapay zeka ile güçlendirilmiş modern blog deneyimi. En güncel içerikler ve teknoloji haberleri.'"),
            ("hero_primary_button_text", "VARCHAR(100) DEFAULT 'Blog Yazılarını Keşfet'"),
            ("hero_primary_button_link", "VARCHAR(200) DEFAULT '#posts'"),
            ("hero_secondary_button_text", "VARCHAR(100) DEFAULT 'Üye Ol'"),
            ("hero_secondary_button_link", "VARCHAR(200) DEFAULT '/register'"),
            ("hero_primary_button_enabled", "BOOLEAN DEFAULT 1"),
            ("hero_secondary_button_enabled", "BOOLEAN DEFAULT 1")
        ]
        
        for column_name, column_def in hero_columns:
            try:
                cursor.execute(f"ALTER TABLE settings ADD COLUMN {column_name} {column_def}")
                print(f"Added hero section column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"Hero section column {column_name} already exists, skipping...")
                else:
                    print(f"Error adding hero section column {column_name}: {e}")
        
        # Update existing settings record with default hero values if they're NULL
        cursor.execute("""
            UPDATE settings 
            SET 
                hero_enabled = COALESCE(hero_enabled, 1),
                hero_title = COALESCE(hero_title, 'AI Destekli Blog Platformu'),
                hero_subtitle = COALESCE(hero_subtitle, 'Yapay zeka ile güçlendirilmiş modern blog deneyimi. En güncel içerikler ve teknoloji haberleri.'),
                hero_primary_button_text = COALESCE(hero_primary_button_text, 'Blog Yazılarını Keşfet'),
                hero_primary_button_link = COALESCE(hero_primary_button_link, '#posts'),
                hero_secondary_button_text = COALESCE(hero_secondary_button_text, 'Üye Ol'),
                hero_secondary_button_link = COALESCE(hero_secondary_button_link, '/register'),
                hero_primary_button_enabled = COALESCE(hero_primary_button_enabled, 1),
                hero_secondary_button_enabled = COALESCE(hero_secondary_button_enabled, 1)
        """)
        
        conn.commit()
        print("Hero section database migration completed successfully!")
        print("\nHero section features added:")
        print("✓ Hero section enable/disable toggle")
        print("✓ Customizable hero title and subtitle")
        print("✓ Primary and secondary button customization")
        print("✓ Button text and link customization")
        print("✓ Individual button enable/disable controls")
        print("\nYou can now customize the hero section from Admin Panel > Site Özelleştirme")
        
    except Exception as e:
        print(f"Error during hero section migration: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
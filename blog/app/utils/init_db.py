import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import User, Settings, Avatar
from app.core.auth import get_password_hash
from app.models import models

def init_database():
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@blog.com",
                hashed_password=get_password_hash("12345678"),
                is_admin=True
            )
            db.add(admin_user)
            print("Admin user created: username='admin', password='12345678'")
        
        settings = db.query(Settings).first()
        if not settings:
            settings = Settings(
                site_title="AI Blog",
                meta_description="A modern AI-powered blog",
                ai_prompt="Write a comprehensive blog post about the given topic. Make it engaging and informative.",
                ai_content_length="medium",
                ai_content_type="informative"
            )
            db.add(settings)
        
        # Add default avatars
        existing_avatars = db.query(Avatar).first()
        if not existing_avatars:
            default_avatars = [
                Avatar(name="Avatar 1", url="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop&crop=face", is_active=True),
                Avatar(name="Avatar 2", url="https://images.unsplash.com/photo-1494790108755-2616c96e6885?w=150&h=150&fit=crop&crop=face", is_active=True),
                Avatar(name="Avatar 3", url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face", is_active=True),
                Avatar(name="Avatar 4", url="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face", is_active=True),
                Avatar(name="Avatar 5", url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face", is_active=True),
                Avatar(name="Avatar 6", url="https://images.unsplash.com/photo-1544723795-3fb6469f5b39?w=150&h=150&fit=crop&crop=face", is_active=True),
            ]
            for avatar in default_avatars:
                db.add(avatar)
        
        db.commit()
        print("Database initialized successfully!")
        print("Admin user created: username='admin', password='12345678'")
        print("Default avatars added for user profiles")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
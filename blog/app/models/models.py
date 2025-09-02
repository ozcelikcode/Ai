from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_admin = Column(Boolean, default=False)
    profile_image = Column(String(200), nullable=True)
    session_duration = Column(Integer, default=1440)  # Default 24 hours in minutes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="user")
    likes = relationship("PostLike", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    posts = relationship("Post", back_populates="category")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    featured_image = Column(String(200), nullable=True)
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(300), nullable=True)
    is_published = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    show_updated_date = Column(Boolean, default=True)
    reading_time = Column(Integer, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    author = relationship("User", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    tags = relationship("PostTag", back_populates="post")
    comments = relationship("Comment", back_populates="post")
    likes = relationship("PostLike", back_populates="post")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    
    posts = relationship("PostTag", back_populates="tag")

class PostTag(Base):
    __tablename__ = "post_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    tag_id = Column(Integer, ForeignKey("tags.id"))
    
    post = relationship("Post", back_populates="tags")
    tag = relationship("Tag", back_populates="posts")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # For reply system
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent")
    post = relationship("Post", back_populates="comments")

class PostLike(Base):
    __tablename__ = "post_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")

class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(300), nullable=True)
    is_published = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    show_updated_date = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MediaFolder(Base):
    __tablename__ = "media_folders"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#944f37")  # Hex color for folder
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    media_files = relationship("Media", back_populates="folder")

class Media(Base):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(200), nullable=False)
    original_name = Column(String(200), nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(300), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    alt_text = Column(String(200), nullable=True)
    width = Column(Integer, nullable=True)  # Image width
    height = Column(Integer, nullable=True)  # Image height
    file_hash = Column(String(64), nullable=True)  # SHA256 hash for duplicate detection
    folder_id = Column(Integer, ForeignKey("media_folders.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    folder = relationship("MediaFolder", back_populates="media_files")

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    site_title = Column(String(200), default="My Blog")
    site_logo = Column(String(200), nullable=True)
    logo_type = Column(String(20), default="text")  # text, image, icon_text, icon
    logo_icon = Column(String(100), nullable=True)
    favicon = Column(String(200), nullable=True)
    meta_description = Column(String(300), nullable=True)
    meta_keywords = Column(String(300), nullable=True)
    footer_copyright = Column(String(500), nullable=True)
    footer_column_1 = Column(Text, nullable=True)
    footer_column_2 = Column(Text, nullable=True)
    footer_column_3 = Column(Text, nullable=True)
    footer_column_order = Column(String(20), default="1,2,3")
    navbar_config = Column(Text, nullable=True)  # JSON config for navbar menu items
    comment_limit = Column(Integer, default=500)
    ai_prompt = Column(Text, default="Write a blog post about the given topic")
    ai_content_length = Column(String(50), default="medium")
    ai_content_type = Column(String(50), default="informative")
    # Hero section settings
    hero_enabled = Column(Boolean, default=True)
    hero_title = Column(String(500), default="AI Destekli Blog Platformu")
    hero_subtitle = Column(Text, default="Yapay zeka ile güçlendirilmiş modern blog deneyimi. En güncel içerikler ve teknoloji haberleri.")
    hero_primary_button_text = Column(String(100), default="Blog Yazılarını Keşfet")
    hero_primary_button_link = Column(String(200), default="#posts")
    hero_secondary_button_text = Column(String(100), default="Üye Ol")
    timezone = Column(String(50), default="Europe/Istanbul")  # Timezone setting
    hero_secondary_button_link = Column(String(200), default="/register")
    hero_primary_button_enabled = Column(Boolean, default=True)
    hero_secondary_button_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Avatar(Base):
    __tablename__ = "avatars"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(300), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AIUsage(Base):
    """AI kullanım verilerini saklamak için model"""
    __tablename__ = "ai_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    usage_type = Column(String(50), nullable=False)  # content, seo, title, bulk
    content_type = Column(String(50), nullable=True)  # blog_post, page, etc.
    topic = Column(String(500), nullable=True)
    prompt_length = Column(Integer, default=0)
    response_length = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)  # seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # İlişki
    user = relationship("User", backref="ai_usage_history")

class AIPreferences(Base):
    """Kullanıcı AI tercihlerini saklamak için model"""
    __tablename__ = "ai_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    default_length = Column(String(20), default="medium")  # short, medium, long
    default_tone = Column(String(20), default="professional")  # professional, casual, technical, educational
    auto_seo = Column(Boolean, default=False)
    auto_tags = Column(Boolean, default=False)
    preferred_language = Column(String(10), default="tr")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # İlişki
    user = relationship("User", backref="ai_preferences", uselist=False)

class AITemplate(Base):
    """AI için önceden hazırlanmış şablonları saklamak için model"""
    __tablename__ = "ai_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    template_type = Column(String(50), nullable=False)  # blog_post, page, seo
    template_content = Column(Text, nullable=False)  # JSON format
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # İlişki
    creator = relationship("User", backref="ai_templates")
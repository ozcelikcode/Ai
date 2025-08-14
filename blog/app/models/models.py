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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="comments")
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
    show_updated_date = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Media(Base):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(200), nullable=False)
    original_name = Column(String(200), nullable=False)
    file_path = Column(String(300), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    alt_text = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    footer_content = Column(Text, nullable=True)
    comment_limit = Column(Integer, default=500)
    ai_prompt = Column(Text, default="Write a blog post about the given topic")
    ai_content_length = Column(String(50), default="medium")
    ai_content_type = Column(String(50), default="informative")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Avatar(Base):
    __tablename__ = "avatars"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(300), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
from sqlalchemy.orm import Session
from app.models.models import Post, Category
from slugify import slugify
import re
from typing import Optional, Type

def generate_slug(title: str, db: Session, model: Type = Post, exclude_id: Optional[int] = None) -> str:
    """Generate unique slug from title"""
    base_slug = slugify(title, lowercase=True)
    slug = base_slug
    counter = 1
    
    while True:
        query = db.query(model).filter(model.slug == slug)
        if exclude_id:
            query = query.filter(model.id != exclude_id)
        
        if not query.first():
            break
            
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

def calculate_reading_time(content: str) -> int:
    """Calculate estimated reading time in minutes"""
    # Remove HTML tags and count words
    text = re.sub(r'<[^>]+>', '', content)
    words = len(text.split())
    
    # Average reading speed is 200-250 words per minute
    reading_time = max(1, round(words / 225))
    return reading_time

def truncate_text(text: str, length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text and return clean text"""
    if not text:
        return ""
    
    # HTML taglerini kaldır
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Çoklu boşlukları tek boşlukla değiştir
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Baş ve sondaki boşlukları temizle
    return clean_text.strip()

def get_excerpt(content: str, length: int = 150) -> str:
    """Get clean excerpt from HTML content"""
    # HTML taglerini temizle
    clean_text = strip_html_tags(content)
    
    # Belirtilen uzunlukta kırp
    if len(clean_text) <= length:
        return clean_text
    
    # Kelime sınırında kırp
    truncated = clean_text[:length]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + '...'
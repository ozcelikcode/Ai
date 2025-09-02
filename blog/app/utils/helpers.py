from sqlalchemy.orm import Session
from app.models.models import Post, Category, Settings
from slugify import slugify
import re
from typing import Optional, Type
from datetime import datetime
import pytz
import hashlib

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

def get_timezone_aware_datetime(dt: datetime, db: Session) -> datetime:
    """Convert datetime to site's timezone"""
    if not dt:
        return dt
    
    # Get timezone setting from database
    settings = db.query(Settings).first()
    timezone_str = settings.timezone if settings and settings.timezone else "Europe/Istanbul"
    
    try:
        # Create timezone object
        site_timezone = pytz.timezone(timezone_str)
        
        # If datetime is naive, assume it's UTC
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        # Convert to site timezone
        return dt.astimezone(site_timezone)
    except Exception:
        # Fallback to original datetime
        return dt

def format_datetime_for_site(dt: datetime, db: Session, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """Format datetime according to site's timezone"""
    if not dt:
        return ""
    
    timezone_aware_dt = get_timezone_aware_datetime(dt, db)
    return timezone_aware_dt.strftime(format_str)

def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA256 hash of file content for duplicate detection"""
    if not file_content:
        return ""
    
    return hashlib.sha256(file_content).hexdigest()

def check_duplicate_media(file_hash: str, file_size: int, db: Session):
    """Check if media file already exists based on hash and size"""
    from app.models.models import Media
    
    if not file_hash:
        return None
    
    # Primary check: file hash
    duplicate = db.query(Media).filter(Media.file_hash == file_hash).first()
    if duplicate:
        return duplicate
    
    # Secondary check: file size (less reliable but helpful)
    duplicates_by_size = db.query(Media).filter(Media.file_size == file_size).all()
    for media in duplicates_by_size:
        # Additional checks could be added here (e.g., image dimensions)
        pass
    
    return None
from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_admin_user
from app.models.models import Post, Category, User, Settings
from app.utils.helpers import generate_slug, calculate_reading_time
from app.utils.ai_content import ai_generator
from app.utils.image_optimizer import optimize_uploaded_image
from datetime import datetime
from typing import Optional, List
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    # Get statistics
    total_posts = db.query(Post).count()
    published_posts = db.query(Post).filter(Post.is_published == True).count()
    draft_posts = db.query(Post).filter(Post.is_draft == True).count()
    total_categories = db.query(Category).count()
    
    from app.models.models import Tag, Page, Comment
    total_tags = db.query(Tag).count() if db.query(Tag).first() else 0
    total_pages = db.query(Page).count() if db.query(Page).first() else 0
    pending_comments = db.query(Comment).filter(Comment.is_approved == False).count() if db.query(Comment).first() else 0
    
    # Get recent posts
    recent_posts = db.query(Post).order_by(Post.created_at.desc()).limit(5).all()
    
    # Get recent comments (if exists)
    recent_comments = []
    if db.query(Comment).first():
        recent_comments = db.query(Comment).order_by(Comment.created_at.desc()).limit(5).all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "admin_user": admin_user,
        "stats": {
            "total_posts": total_posts,
            "published_posts": published_posts,
            "draft_posts": draft_posts,
            "total_categories": total_categories,
            "total_tags": total_tags,
            "total_pages": total_pages,
            "pending_comments": pending_comments
        },
        "recent_posts": recent_posts,
        "recent_comments": recent_comments
    })

@router.get("/posts", response_class=HTMLResponse)
async def admin_posts(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    try:
        from sqlalchemy.orm import joinedload
        
        # Use eager loading for better performance and to avoid lazy loading issues
        posts = db.query(Post).options(
            joinedload(Post.category),
            joinedload(Post.author)
        ).order_by(Post.created_at.desc()).all()
        
        return templates.TemplateResponse("admin/posts.html", {
            "request": request,
            "admin_user": admin_user,
            "posts": posts
        })
    except Exception as e:
        # Log the error (in production you'd use proper logging)
        print(f"Admin posts error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return with empty posts list to prevent 500 error
        return templates.TemplateResponse("admin/posts.html", {
            "request": request,
            "admin_user": admin_user,
            "posts": [],
            "error_message": "Yazılar yüklenirken bir hata oluştu. Lütfen tekrar deneyin."
        })

@router.get("/posts/new", response_class=HTMLResponse)
async def new_post_form(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    try:
        categories = db.query(Category).all()
        return templates.TemplateResponse("admin/post_form.html", {
            "request": request,
            "admin_user": admin_user,
            "categories": categories,
            "post": None
        })
    except Exception as e:
        print(f"Error loading new post form: {e}")
        return templates.TemplateResponse("admin/post_form.html", {
            "request": request,
            "admin_user": admin_user,
            "categories": [],
            "post": None,
            "error_message": "Form yüklenirken hata oluştu."
        })

@router.post("/posts/upload-featured-image")
async def upload_featured_image(
    featured_image: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
):
    """Post için featured image yükle ve optimize et"""
    try:
        # File validation
        if not featured_image.content_type.startswith('image/'):
            return JSONResponse({"success": False, "error": "Sadece resim dosyaları yükleyebilirsiniz"})
        
        # Read file content
        file_content = await featured_image.read()
        
        # File size check (5MB limit for featured images)
        if len(file_content) > 5 * 1024 * 1024:
            return JSONResponse({"success": False, "error": "Resim dosyası çok büyük (max 5MB)"})
        
        # Create upload directory
        upload_dir = Path("uploads/featured")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Optimize image for featured images (hero size)
        optimized_bytes, extension = optimize_uploaded_image(
            file_content,
            featured_image.filename,
            max_width=1920,  # Hero image size
            max_height=1080,
            quality=90  # Higher quality for featured images
        )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{extension}"
        file_path = upload_dir / unique_filename
        
        # Save optimized image
        with open(file_path, "wb") as f:
            f.write(optimized_bytes)
        
        # Return URL for the uploaded image
        image_url = f"/uploads/featured/{unique_filename}"
        
        return JSONResponse({
            "success": True,
            "url": image_url,
            "filename": unique_filename,
            "original_size": len(file_content),
            "optimized_size": len(optimized_bytes)
        })
        
    except Exception as e:
        print(f"Featured image upload error: {e}")
        return JSONResponse({"success": False, "error": "Resim yüklenirken bir hata oluştu"})

@router.post("/posts/new")
async def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(""),
    category_id: int = Form(None),
    action: str = Form("draft"),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    featured_image: str = Form(""),
    selected_media_url: str = Form(""),
    tags: List[str] = Form([]),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Tag, PostTag
    
    # Action'a göre publish durumunu belirle
    is_published = action == "publish"
    is_draft = action == "draft"
    
    slug = generate_slug(title, db)
    reading_time = calculate_reading_time(content)
    
    post = Post(
        title=title,
        slug=slug,
        content=content,
        excerpt=excerpt or content[:200] + "...",
        category_id=category_id if category_id else None,
        is_published=is_published,
        is_draft=is_draft,
        meta_title=meta_title or title,
        meta_description=meta_description or excerpt[:160],
        featured_image=featured_image or None,
        reading_time=reading_time,
        author_id=admin_user.id,
        published_at=datetime.utcnow() if is_published else None
    )
    
    db.add(post)
    db.commit()
    
    # Handle tags
    for tag_name in tags:
        if tag_name.strip():
            # Get or create tag
            tag = db.query(Tag).filter(Tag.name == tag_name.strip()).first()
            if not tag:
                tag_slug = generate_slug(tag_name.strip(), db, Tag)
                tag = Tag(name=tag_name.strip(), slug=tag_slug)
                db.add(tag)
                db.commit()
            
            # Create post-tag relationship
            post_tag = PostTag(post_id=post.id, tag_id=tag.id)
            db.add(post_tag)
    
    db.commit()
    
    return RedirectResponse(url="/admin/posts", status_code=303)

@router.get("/posts/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_form(request: Request, post_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    categories = db.query(Category).all()
    return templates.TemplateResponse("admin/post_form.html", {
        "request": request,
        "admin_user": admin_user,
        "categories": categories,
        "post": post
    })

@router.post("/posts/{post_id}/edit")
async def update_post(
    request: Request,
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(""),
    category_id: int = Form(None),
    action: str = Form("draft"),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    featured_image: str = Form(""),
    tags: List[str] = Form([]),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Tag, PostTag
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Action'a göre publish durumunu belirle
    is_published = action == "publish"
    is_draft = action == "draft"
    
    # Update slug if title changed
    if post.title != title:
        post.slug = generate_slug(title, db, exclude_id=post_id)
    
    post.title = title
    post.content = content
    post.excerpt = excerpt or content[:200] + "..."
    post.category_id = category_id if category_id else None
    post.is_published = is_published
    post.is_draft = is_draft
    post.meta_title = meta_title or title
    post.meta_description = meta_description or excerpt[:160]
    post.featured_image = featured_image or None
    post.reading_time = calculate_reading_time(content)
    
    if is_published and not post.published_at:
        post.published_at = datetime.utcnow()
    
    # Handle tags - remove existing ones first
    db.query(PostTag).filter(PostTag.post_id == post.id).delete()
    
    # Add new tags
    for tag_name in tags:
        if tag_name.strip():
            # Get or create tag
            tag = db.query(Tag).filter(Tag.name == tag_name.strip()).first()
            if not tag:
                tag_slug = generate_slug(tag_name.strip(), db, Tag)
                tag = Tag(name=tag_name.strip(), slug=tag_slug)
                db.add(tag)
                db.commit()
            
            # Create post-tag relationship
            post_tag = PostTag(post_id=post.id, tag_id=tag.id)
            db.add(post_tag)
    
    db.commit()
    
    return RedirectResponse(url="/admin/posts", status_code=303)

@router.post("/posts/{post_id}/delete")
async def delete_post(post_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Delete related records first to avoid foreign key constraints
        from app.models.models import PostTag, Comment, PostLike
        
        # Delete post tags
        db.query(PostTag).filter(PostTag.post_id == post_id).delete()
        
        # Delete comments
        db.query(Comment).filter(Comment.post_id == post_id).delete()
        
        # Delete likes
        db.query(PostLike).filter(PostLike.post_id == post_id).delete()
        
        # Now delete the post
        db.delete(post)
        db.commit()
        
        return RedirectResponse(url="/admin/posts", status_code=303)
    except Exception as e:
        print(f"Error deleting post: {e}")
        db.rollback()
        return RedirectResponse(url="/admin/posts?error=delete_failed", status_code=303)

@router.get("/categories", response_class=HTMLResponse)
async def admin_categories(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return templates.TemplateResponse("admin/categories.html", {
        "request": request,
        "admin_user": admin_user,
        "categories": categories
    })

@router.post("/categories/new")
async def create_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    slug = generate_slug(name, db, model=Category)
    
    category = Category(
        name=name,
        slug=slug,
        description=description
    )
    
    db.add(category)
    db.commit()
    
    return RedirectResponse(url="/admin/categories", status_code=303)

@router.post("/categories/{category_id}/edit")
async def edit_category(
    category_id: int,
    name: str = Form(...),
    description: str = Form(""),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update slug if name changed
    if category.name != name:
        category.slug = generate_slug(name, db, model=Category, exclude_id=category_id)
    
    category.name = name
    category.description = description
    
    db.commit()
    
    return RedirectResponse(url="/admin/categories", status_code=303)

@router.post("/categories/{category_id}/delete")
async def delete_category(category_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(category)
    db.commit()
    
    return RedirectResponse(url="/admin/categories", status_code=303)

# Page Management Routes
@router.get("/pages", response_class=HTMLResponse)
async def admin_pages(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    from app.models.models import Page
    pages = db.query(Page).order_by(Page.created_at.desc()).all()
    return templates.TemplateResponse("admin/pages.html", {
        "request": request,
        "admin_user": admin_user,
        "pages": pages
    })

@router.get("/pages/new", response_class=HTMLResponse)
async def new_page_form(request: Request, admin_user: User = Depends(get_admin_user)):
    return templates.TemplateResponse("admin/page_form.html", {
        "request": request,
        "admin_user": admin_user,
        "page": None
    })

@router.post("/pages/new")
async def create_page(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    action: str = Form("draft"),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    show_updated_date: bool = Form(True),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Page
    
    # Action'a göre publish durumunu belirle
    is_published = action == "publish"
    
    slug = generate_slug(title, db, model=Page)
    
    page = Page(
        title=title,
        slug=slug,
        content=content,
        meta_title=meta_title or title,
        meta_description=meta_description or content[:160],
        is_published=is_published,
        show_updated_date=show_updated_date
    )
    
    db.add(page)
    db.commit()
    
    return RedirectResponse(url="/admin/pages", status_code=303)

@router.get("/pages/{page_id}/edit", response_class=HTMLResponse)
async def edit_page_form(request: Request, page_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    from app.models.models import Page
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return templates.TemplateResponse("admin/page_form.html", {
        "request": request,
        "admin_user": admin_user,
        "page": page
    })

@router.post("/pages/{page_id}/edit")
async def update_page(
    request: Request,
    page_id: int,
    title: str = Form(...),
    content: str = Form(...),
    action: str = Form("draft"),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    show_updated_date: bool = Form(True),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Page
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Action'a göre publish durumunu belirle
    is_published = action == "publish"
    
    # Update slug if title changed
    if page.title != title:
        page.slug = generate_slug(title, db, model=Page, exclude_id=page_id)
    
    page.title = title
    page.content = content
    page.is_published = is_published
    page.meta_title = meta_title or title
    page.meta_description = meta_description or content[:160]
    page.show_updated_date = show_updated_date
    
    db.commit()
    
    return RedirectResponse(url="/admin/pages", status_code=303)

@router.post("/pages/{page_id}/delete")
async def delete_page(page_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    from app.models.models import Page
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    db.delete(page)
    db.commit()
    
    return RedirectResponse(url="/admin/pages", status_code=303)

# AI Content Generation Routes
@router.post("/ai/generate-content")
async def generate_ai_content(
    request: Request,
    topic: str = Form(...),
    content_length: str = Form("medium"),
    content_type: str = Form("informative"),
    custom_prompt: str = Form(""),
    admin_user: User = Depends(get_admin_user)
):
    """Generate AI content for a blog post"""
    try:
        result = ai_generator.generate_blog_post(
            topic=topic,
            content_length=content_length,
            content_type=content_type,
            custom_prompt=custom_prompt if custom_prompt else None
        )
        
        return JSONResponse(result)
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@router.post("/ai/generate-titles")
async def generate_ai_titles(
    request: Request,
    topic: str = Form(...),
    count: int = Form(5),
    admin_user: User = Depends(get_admin_user)
):
    """Generate AI title suggestions"""
    try:
        titles = ai_generator.generate_title_suggestions(topic, count)
        
        return JSONResponse({
            "success": True,
            "titles": titles
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@router.post("/ai/improve-content")
async def improve_ai_content(
    request: Request,
    content: str = Form(...),
    instruction: str = Form(...),
    admin_user: User = Depends(get_admin_user)
):
    """Improve existing content with AI"""
    try:
        improved_content = ai_generator.improve_content(content, instruction)
        
        return JSONResponse({
            "success": True,
            "content": improved_content
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

# Settings Routes
@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    settings = db.query(Settings).first()
    from app.models.models import Avatar
    avatars = db.query(Avatar).filter(Avatar.is_active == True).all()
    
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "admin_user": admin_user,
        "settings": settings,
        "avatars": avatars
    })

@router.post("/settings/save")
async def save_settings(
    request: Request,
    site_title: str = Form(...),
    site_logo: str = Form(""),
    logo_type: str = Form("text"),
    logo_icon: str = Form(""),
    favicon: str = Form(""),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    comment_limit: int = Form(500),
    footer_content: str = Form(""),
    ai_prompt: str = Form(""),
    ai_content_length: str = Form("medium"),
    ai_content_type: str = Form("informative"),
    logo_file: UploadFile = File(None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    settings = db.query(Settings).first()
    
    if not settings:
        settings = Settings()
        db.add(settings)
    
    # Handle logo file upload
    logo_url = site_logo
    if logo_file and logo_file.filename:
        if not logo_file.content_type.startswith('image/'):
            return JSONResponse({"success": False, "error": "Sadece resim dosyaları yükleyebilirsiniz"})
        
        # Create upload directory
        upload_dir = Path("uploads/site")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(logo_file.filename)[1]
        unique_filename = f"logo_{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        file_content = await logo_file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logo_url = f"/uploads/site/{unique_filename}"
    
    settings.site_title = site_title
    settings.site_logo = logo_url if logo_url else None
    settings.logo_type = logo_type
    settings.logo_icon = logo_icon if logo_icon else None
    settings.favicon = favicon if favicon else None
    settings.meta_description = meta_description if meta_description else None
    settings.meta_keywords = meta_keywords if meta_keywords else None
    settings.comment_limit = comment_limit
    settings.footer_content = footer_content if footer_content else None
    settings.ai_prompt = ai_prompt if ai_prompt else "Write a blog post about the given topic"
    settings.ai_content_length = ai_content_length
    settings.ai_content_type = ai_content_type
    
    db.commit()
    
    return RedirectResponse(url="/admin/settings?success=1", status_code=303)

# Site Customization Routes
@router.get("/customize", response_class=HTMLResponse)
async def admin_customize(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    settings = db.query(Settings).first()
    
    # Create default settings if not exists
    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
    
    return templates.TemplateResponse("admin/customize.html", {
        "request": request,
        "admin_user": admin_user,
        "settings": settings
    })

@router.post("/customize/save")
async def save_customization(
    request: Request,
    logo_type: str = Form("text"),
    logo_icon: str = Form(""),
    site_logo: str = Form(""),
    footer_content: str = Form(""),
    logo_file: UploadFile = File(None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    settings = db.query(Settings).first()
    
    if not settings:
        settings = Settings()
        db.add(settings)
    
    # Handle logo file upload
    logo_url = site_logo
    if logo_file and logo_file.filename:
        if not logo_file.content_type.startswith('image/'):
            return JSONResponse({"success": False, "error": "Sadece resim dosyaları yükleyebilirsiniz"})
        
        # Create upload directory
        upload_dir = Path("uploads/site")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(logo_file.filename)[1]
        unique_filename = f"logo_{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        file_content = await logo_file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logo_url = f"/uploads/site/{unique_filename}"
    
    settings.logo_type = logo_type
    settings.logo_icon = logo_icon if logo_icon else None
    settings.site_logo = logo_url if logo_url else None
    settings.footer_content = footer_content if footer_content else None
    
    db.commit()
    
    return RedirectResponse(url="/admin/customize?success=1", status_code=303)

# Tag Management Routes
@router.get("/tags", response_class=HTMLResponse)
async def admin_tags(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    from app.models.models import Tag
    tags = db.query(Tag).all()
    return templates.TemplateResponse("admin/tags.html", {
        "request": request,
        "admin_user": admin_user,
        "tags": tags
    })

@router.post("/tags/new")
async def create_tag(
    request: Request,
    name: str = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Tag
    
    slug = generate_slug(name, db, model=Tag)
    
    tag = Tag(
        name=name,
        slug=slug
    )
    
    db.add(tag)
    db.commit()
    
    return RedirectResponse(url="/admin/tags", status_code=303)

@router.post("/tags/{tag_id}/edit")
async def edit_tag(
    tag_id: int,
    name: str = Form(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Tag
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Update slug if name changed
    if tag.name != name:
        tag.slug = generate_slug(name, db, model=Tag, exclude_id=tag_id)
    
    tag.name = name
    
    db.commit()
    
    return RedirectResponse(url="/admin/tags", status_code=303)

@router.post("/tags/{tag_id}/delete")
async def delete_tag(tag_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    from app.models.models import Tag
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag)
    db.commit()
    
    return RedirectResponse(url="/admin/tags", status_code=303)

# API Routes for Media Gallery
@router.get("/api/media")
async def get_media_files(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get all media files for gallery"""
    from app.models.models import Media
    media_files = db.query(Media).order_by(Media.created_at.desc()).all()
    
    return JSONResponse({
        "success": True,
        "media": [{
            "id": media.id,
            "filename": media.filename,
            "original_name": media.original_name,
            "file_path": media.file_path,
            "mime_type": media.mime_type,
            "alt_text": media.alt_text,
            "created_at": media.created_at.isoformat()
        } for media in media_files]
    })

@router.get("/api/tags/search")
async def search_tags(q: str = "", admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Search tags for autocomplete"""
    from app.models.models import Tag
    
    if not q or len(q.strip()) < 2:
        return JSONResponse({"tags": []})
    
    tags = db.query(Tag).filter(Tag.name.ilike(f"%{q}%")).limit(10).all()
    
    return JSONResponse({
        "tags": [{"id": tag.id, "name": tag.name} for tag in tags]
    })

# Avatar Management Routes
@router.get("/avatars/list")
async def list_avatars(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    from app.models.models import Avatar
    avatars = db.query(Avatar).filter(Avatar.is_active == True).all()
    return JSONResponse({
        "success": True,
        "avatars": [{"id": str(avatar.id), "url": avatar.url, "name": avatar.name} for avatar in avatars]
    })

@router.post("/avatars/add")
async def add_avatar(
    request: Request,
    url: str = Form(""),
    file: UploadFile = File(None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Avatar
    
    avatar_url = url
    avatar_name = ""
    
    if file:
        # Handle file upload
        if not file.content_type.startswith('image/'):
            return JSONResponse({"success": False, "error": "Only image files are allowed"})
        
        # Create uploads directory if it doesn't exist
        upload_dir = "static/uploads/avatars"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"avatar_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        avatar_url = f"/static/uploads/avatars/{filename}"
        avatar_name = file.filename
    elif url:
        avatar_name = f"Avatar {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    else:
        return JSONResponse({"success": False, "error": "URL or file required"})
    
    avatar = Avatar(
        name=avatar_name,
        url=avatar_url,
        is_active=True
    )
    
    db.add(avatar)
    db.commit()
    
    return JSONResponse({"success": True})

@router.post("/avatars/{avatar_id}/delete")
async def delete_avatar(avatar_id: int, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    from app.models.models import Avatar
    avatar = db.query(Avatar).filter(Avatar.id == avatar_id).first()
    if not avatar:
        return JSONResponse({"success": False, "error": "Avatar not found"})
    
    # Mark as inactive instead of deleting (in case users are using this avatar)
    avatar.is_active = False
    db.commit()
    
    return JSONResponse({"success": True})
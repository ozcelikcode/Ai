from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import get_db
from app.core.auth import get_current_user_optional
from app.models.models import Post, Category, Page, Tag, PostTag, Settings
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_template_context(request: Request, db: Session, current_user=None):
    """Get common template context including site settings"""
    site_settings = db.query(Settings).first()
    context = {
        "request": request,
        "site_settings": site_settings
    }
    if current_user is not None:
        context["current_user"] = current_user
    return context

@router.get("/post/{slug}", response_class=HTMLResponse)
async def post_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    try:
        post = db.query(Post).filter(Post.slug == slug, Post.is_published == True).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        current_user = get_current_user_optional(request, db)
        
        # Get context with settings
        context = get_template_context(request, db, current_user)
        
        # Get sidebar data safely
        categories_data = []
        popular_posts = []
        tags = []
        
        try:
            # Get categories with post counts
            categories = db.query(Category).all()
            for category in categories:
                post_count = db.query(Post).filter(
                    Post.category_id == category.id,
                    Post.is_published == True
                ).count()
                categories_data.append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'post_count': post_count
                })
        except:
            categories_data = []
        
        try:
            # Get popular posts (recent published posts)
            popular_posts = db.query(Post).filter(
                Post.is_published == True
            ).order_by(Post.created_at.desc()).limit(5).all()
        except:
            popular_posts = []
        
        try:
            # Get all tags
            tags = db.query(Tag).all()
        except:
            tags = []
        
        # Add post data and sidebar data for template
        context.update({
            "post": post,
            "related_posts": [],
            "categories": categories_data,
            "popular_posts": popular_posts,
            "tags": tags,
            "archives": []
        })
        
        return templates.TemplateResponse("blog/post_detail.html", context)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Post detail error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/categories", response_class=HTMLResponse)
async def categories_list(request: Request, db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    current_user = get_current_user_optional(request, db)
    
    context = get_template_context(request, db, current_user)
    context["categories"] = categories
    return templates.TemplateResponse("blog/categories.html", context)

@router.get("/category/{slug}", response_class=HTMLResponse)
async def category_posts(request: Request, slug: str, db: Session = Depends(get_db)):
    try:
        category = db.query(Category).filter(Category.slug == slug).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        posts = db.query(Post).filter(
            Post.category_id == category.id,
            Post.is_published == True
        ).order_by(Post.created_at.desc()).all()
        
        current_user = get_current_user_optional(request, db)
        
        # Get context with settings
        context = get_template_context(request, db, current_user)
        
        # Get sidebar data safely
        categories_data = []
        popular_posts = []
        tags = []
        
        try:
            # Get categories with post counts
            categories = db.query(Category).all()
            for cat in categories:
                post_count = db.query(Post).filter(
                    Post.category_id == cat.id,
                    Post.is_published == True
                ).count()
                categories_data.append({
                    'id': cat.id,
                    'name': cat.name,
                    'slug': cat.slug,
                    'post_count': post_count
                })
        except:
            categories_data = []
        
        try:
            # Get popular posts (recent published posts)
            popular_posts = db.query(Post).filter(
                Post.is_published == True
            ).order_by(Post.created_at.desc()).limit(5).all()
        except:
            popular_posts = []
        
        try:
            # Get all tags
            tags = db.query(Tag).all()
        except:
            tags = []
        
        context.update({
            "category": category,
            "posts": posts,
            "categories": categories_data,
            "popular_posts": popular_posts,
            "tags": tags
        })
        return templates.TemplateResponse("blog/category_posts.html", context)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Category posts error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{slug}", response_class=HTMLResponse)
async def page_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.slug == slug, Page.is_published == True).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    current_user = get_current_user_optional(request, db)
    
    context = get_template_context(request, db, current_user)
    context["page"] = page
    return templates.TemplateResponse("blog/page_detail.html", context)

@router.get("/tag/{slug}", response_class=HTMLResponse)
async def tag_posts(request: Request, slug: str, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.slug == slug).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Get posts with this tag
    posts = db.query(Post).join(PostTag).filter(
        PostTag.tag_id == tag.id,
        Post.is_published == True
    ).order_by(Post.created_at.desc()).all()
    
    current_user = get_current_user_optional(request, db)
    
    context = get_template_context(request, db, current_user)
    context.update({
        "tag": tag,
        "posts": posts
    })
    return templates.TemplateResponse("blog/tag_posts.html", context)

@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    
    context = get_template_context(request, db, current_user)
    return templates.TemplateResponse("blog/about.html", context)

@router.get("/archive/{year}/{month}", response_class=HTMLResponse)
async def archive_posts(request: Request, year: str, month: str, db: Session = Depends(get_db)):
    """Show posts from a specific month and year"""
    from sqlalchemy import func
    
    posts = db.query(Post).filter(
        func.strftime('%Y', Post.created_at) == year,
        func.strftime('%m', Post.created_at) == month,
        Post.is_published == True
    ).order_by(Post.created_at.desc()).all()
    
    current_user = get_current_user_optional(request, db)
    
    month_names = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                   'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    
    context = get_template_context(request, db, current_user)
    context.update({
        "posts": posts,
        "year": year,
        "month": month,
        "month_name": month_names[int(month)],
        "archive_title": f"{month_names[int(month)]} {year} Arşivi"
    })
    return templates.TemplateResponse("blog/archive.html", context)

@router.get("/sitemap.xml")
async def sitemap(request: Request, db: Session = Depends(get_db)):
    """Generate XML sitemap for SEO"""
    from fastapi.responses import Response
    
    # Get all published posts
    posts = db.query(Post).filter(Post.is_published == True).all()
    categories = db.query(Category).all()
    pages = db.query(Page).filter(Page.is_published == True).all()
    tags = db.query(Tag).all()
    
    base_url = str(request.base_url).rstrip('/')
    
    sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{base_url}/about</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/categories</loc>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>'''
    
    # Add posts
    for post in posts:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}/post/{post.slug}</loc>
        <lastmod>{post.updated_at.strftime('%Y-%m-%d') if post.updated_at else post.created_at.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>'''
    
    # Add categories
    for category in categories:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}/category/{category.slug}</loc>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>'''
    
    # Add pages
    for page in pages:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}/page/{page.slug}</loc>
        <lastmod>{page.updated_at.strftime('%Y-%m-%d') if page.updated_at else page.created_at.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>'''
    
    # Add tags
    for tag in tags:
        sitemap_xml += f'''
    <url>
        <loc>{base_url}/tag/{tag.slug}</loc>
        <changefreq>weekly</changefreq>
        <priority>0.5</priority>
    </url>'''
    
    sitemap_xml += '''
</urlset>'''
    
    return Response(content=sitemap_xml, media_type="application/xml")

@router.get("/robots.txt")
async def robots_txt(request: Request):
    """Generate robots.txt for SEO"""
    from fastapi.responses import Response
    
    base_url = str(request.base_url).rstrip('/')
    robots_content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Disallow: /uploads/

Sitemap: {base_url}/sitemap.xml
"""
    
    return Response(content=robots_content, media_type="text/plain")
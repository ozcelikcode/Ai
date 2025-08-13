from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user_optional
from app.models.models import Post, Category, Page, Tag, PostTag
from typing import Optional

router = APIRouter()
from app.core.templates import templates

@router.get("/post/{slug}", response_class=HTMLResponse)
async def post_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.slug == slug, Post.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    current_user = get_current_user_optional(request, db)
    
    # Get related posts
    related_posts = db.query(Post).filter(
        Post.category_id == post.category_id,
        Post.id != post.id,
        Post.is_published == True
    ).limit(3).all()
    
    return templates.TemplateResponse("blog/post_detail.html", {
        "request": request,
        "post": post,
        "current_user": current_user,
        "related_posts": related_posts
    })

@router.get("/categories", response_class=HTMLResponse)
async def categories_list(request: Request, db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    current_user = get_current_user_optional(request, db)
    
    return templates.TemplateResponse("blog/categories.html", {
        "request": request,
        "categories": categories,
        "current_user": current_user
    })

@router.get("/category/{slug}", response_class=HTMLResponse)
async def category_posts(request: Request, slug: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    posts = db.query(Post).filter(
        Post.category_id == category.id,
        Post.is_published == True
    ).order_by(Post.created_at.desc()).all()
    
    current_user = get_current_user_optional(request, db)
    
    return templates.TemplateResponse("blog/category_posts.html", {
        "request": request,
        "category": category,
        "posts": posts,
        "current_user": current_user
    })

@router.get("/{slug}", response_class=HTMLResponse)
async def page_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.slug == slug, Page.is_published == True).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    current_user = get_current_user_optional(request, db)
    
    return templates.TemplateResponse("blog/page_detail.html", {
        "request": request,
        "page": page,
        "current_user": current_user
    })

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
    
    return templates.TemplateResponse("blog/tag_posts.html", {
        "request": request,
        "tag": tag,
        "posts": posts,
        "current_user": current_user
    })

@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    
    return templates.TemplateResponse("blog/about.html", {
        "request": request,
        "current_user": current_user
    })

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
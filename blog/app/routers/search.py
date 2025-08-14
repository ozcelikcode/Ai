from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.database import get_db
from app.core.auth import get_current_user_optional
from app.models.models import Post, Category, Tag, PostTag
from typing import Optional

router = APIRouter(tags=["search"])
templates = Jinja2Templates(directory="templates")

@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: str = Query("", description="Search query"),
    category: Optional[str] = Query(None, description="Category filter"),
    db: Session = Depends(get_db)
):
    """Search page with results"""
    current_user = get_current_user_optional(request, db)
    results = []
    categories = db.query(Category).all()
    
    if q.strip():
        results = search_posts(db, q, category)
    
    return templates.TemplateResponse("blog/search.html", {
        "request": request,
        "current_user": current_user,
        "query": q,
        "category_filter": category,
        "results": results,
        "categories": categories,
        "result_count": len(results)
    })

@router.get("/api/search")
async def search_api(
    q: str = Query("", description="Search query"),
    category: Optional[str] = Query(None, description="Category filter"),
    limit: int = Query(10, description="Results limit"),
    db: Session = Depends(get_db)
):
    """API endpoint for search"""
    if not q.strip():
        return JSONResponse({
            "success": False,
            "message": "Search query is required",
            "results": []
        })
    
    results = search_posts(db, q, category, limit)
    
    return JSONResponse({
        "success": True,
        "query": q,
        "category": category,
        "results": [{
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "excerpt": post.excerpt,
            "category": post.category.name if post.category else None,
            "category_slug": post.category.slug if post.category else None,
            "author": post.author.username,
            "created_at": post.created_at.strftime('%d.%m.%Y'),
            "reading_time": post.reading_time,
            "url": f"/post/{post.slug}"
        } for post in results]
    })

def search_posts(db: Session, query: str, category_filter: Optional[str] = None, limit: int = 50):
    """Search posts by title, content, and tags"""
    search_terms = query.strip().split()
    
    # Base query for published posts
    base_query = db.query(Post).filter(Post.is_published == True)
    
    # Category filter
    if category_filter:
        category = db.query(Category).filter(Category.slug == category_filter).first()
        if category:
            base_query = base_query.filter(Post.category_id == category.id)
    
    # Search conditions
    search_conditions = []
    
    for term in search_terms:
        term_pattern = f"%{term}%"
        
        # Search in title, content, excerpt
        content_conditions = [
            Post.title.ilike(term_pattern),
            Post.content.ilike(term_pattern),
            Post.excerpt.ilike(term_pattern)
        ]
        
        search_conditions.append(or_(*content_conditions))
    
    # Combine all search terms with AND
    if search_conditions:
        base_query = base_query.filter(and_(*search_conditions))
    
    # Order by relevance (title matches first, then by date)
    results = base_query.order_by(
        Post.title.ilike(f"%{query}%").desc(),
        Post.created_at.desc()
    ).limit(limit).all()
    
    return results

@router.get("/api/search/suggestions")
async def search_suggestions(
    q: str = Query("", description="Search query"),
    db: Session = Depends(get_db)
):
    """Get search suggestions"""
    if len(q.strip()) < 2:
        return JSONResponse({"suggestions": []})
    
    # Get post titles that match
    post_suggestions = db.query(Post.title).filter(
        Post.is_published == True,
        Post.title.ilike(f"%{q}%")
    ).limit(5).all()
    
    # Get category names that match
    category_suggestions = db.query(Category.name).filter(
        Category.name.ilike(f"%{q}%")
    ).limit(3).all()
    
    suggestions = []
    
    # Add post titles
    for post in post_suggestions:
        suggestions.append({
            "text": post.title,
            "type": "post"
        })
    
    # Add categories
    for category in category_suggestions:
        suggestions.append({
            "text": category.name,
            "type": "category"
        })
    
    return JSONResponse({"suggestions": suggestions[:8]})

# Admin search routes
admin_router = APIRouter(prefix="/admin", tags=["admin-search"])

@admin_router.get("/api/search/posts")
async def admin_search_posts(
    q: str = Query("", description="Search query"),
    status: str = Query("all", description="Post status filter"),
    db: Session = Depends(get_db)
):
    """Admin search for posts"""
    if not q.strip():
        return JSONResponse({"results": []})
    
    query_obj = db.query(Post)
    
    # Status filter
    if status == "published":
        query_obj = query_obj.filter(Post.is_published == True)
    elif status == "draft":
        query_obj = query_obj.filter(Post.is_published == False)
    
    # Search
    search_pattern = f"%{q}%"
    results = query_obj.filter(
        or_(
            Post.title.ilike(search_pattern),
            Post.content.ilike(search_pattern)
        )
    ).order_by(Post.created_at.desc()).limit(20).all()
    
    return JSONResponse({
        "results": [{
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "status": "Yayında" if post.is_published else "Taslak",
            "created_at": post.created_at.strftime('%d.%m.%Y'),
            "url": f"/admin/posts/{post.id}/edit"
        } for post in results]
    })

def get_search_routers():
    """Return both public and admin search routers"""
    return [router, admin_router]
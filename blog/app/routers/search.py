from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.core.database import get_db
from app.core.auth import get_current_user_optional
from app.models.models import Post, Category, Tag, PostTag, Settings
from typing import Optional

router = APIRouter(tags=["search"])
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

@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: str = Query("", description="Search query"),
    category: Optional[str] = Query(None, description="Category filter"),
    db: Session = Depends(get_db)
):
    """Search page with results"""
    try:
        current_user = get_current_user_optional(request, db)
        results = []
        categories = []
        
        # Get categories safely
        try:
            categories = db.query(Category).all()
        except:
            categories = []
        
        # Search if query provided
        if q.strip():
            try:
                results = search_posts(db, q, category)
            except:
                results = []
        
        context = get_template_context(request, db, current_user)
        context.update({
            "query": q,
            "category_filter": category,
            "results": results,
            "categories": categories,
            "result_count": len(results)
        })
        return templates.TemplateResponse("blog/search.html", context)
        
    except Exception as e:
        print(f"Search page error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Search error")

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
    """Search posts by title, content, and tags - simplified"""
    try:
        search_pattern = f"%{query.strip()}%"
        
        # Base query for published posts
        base_query = db.query(Post).filter(Post.is_published == True)
        
        # Category filter
        if category_filter:
            try:
                category = db.query(Category).filter(Category.slug == category_filter).first()
                if category:
                    base_query = base_query.filter(Post.category_id == category.id)
            except:
                pass
        
        # Simple search in title and content
        try:
            results = base_query.filter(
                or_(
                    Post.title.ilike(search_pattern),
                    Post.content.ilike(search_pattern)
                )
            ).order_by(Post.created_at.desc()).limit(limit).all()
            
            return results
        except Exception as e:
            print(f"Search query error: {e}")
            return []
            
    except Exception as e:
        print(f"Search function error: {e}")
        return []

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
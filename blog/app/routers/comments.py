from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, get_admin_user, get_current_user_optional
from app.models.models import Comment, Post, User, Settings
from datetime import datetime
from typing import Optional

router = APIRouter(tags=["comments"])
templates = Jinja2Templates(directory="templates")

@router.post("/post/{slug}/comment")
async def add_comment(
    slug: str,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a post"""
    post = db.query(Post).filter(Post.slug == slug, Post.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check comment character limit
    settings = db.query(Settings).first()
    comment_limit = settings.comment_limit if settings else 500
    
    if len(content.strip()) > comment_limit:
        raise HTTPException(status_code=400, detail=f"Yorum {comment_limit} karakterden uzun olamaz")
    
    if len(content.strip()) < 1:
        raise HTTPException(status_code=400, detail="Yorum boş olamaz")
    
    comment = Comment(
        content=content.strip(),
        user_id=current_user.id,
        post_id=post.id,
        is_approved=current_user.is_admin  # Admins don't need approval
    )
    
    db.add(comment)
    db.commit()
    
    return RedirectResponse(url=f"/post/{slug}#comments", status_code=303)

@router.get("/api/post/{slug}/comments")
async def get_post_comments(
    slug: str, 
    db: Session = Depends(get_db)
):
    """Get approved comments for a post"""
    post = db.query(Post).filter(Post.slug == slug, Post.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comments = db.query(Comment).filter(
        Comment.post_id == post.id,
        Comment.is_approved == True
    ).order_by(Comment.created_at.asc()).all()
    
    return JSONResponse({
        "comments": [{
            "id": comment.id,
            "content": comment.content,
            "user": {
                "username": comment.user.username,
                "profile_image": comment.user.profile_image
            },
            "created_at": comment.created_at.strftime("%d.%m.%Y %H:%M")
        } for comment in comments]
    })

# Admin routes for comment management
admin_router = APIRouter(prefix="/admin", tags=["admin-comments"])

@admin_router.get("/comments", response_class=HTMLResponse)
async def admin_comments(
    request: Request,
    status: str = "pending",  # pending, approved, all
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Admin comments management page"""
    query = db.query(Comment).join(Comment.post).join(Comment.user)
    
    if status == "pending":
        query = query.filter(Comment.is_approved == False)
    elif status == "approved":
        query = query.filter(Comment.is_approved == True)
    
    comments = query.order_by(Comment.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/comments.html", {
        "request": request,
        "admin_user": admin_user,
        "comments": comments,
        "current_status": status
    })

@admin_router.post("/comments/{comment_id}/approve")
async def approve_comment(
    comment_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Approve a comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.is_approved = True
    db.commit()
    
    return JSONResponse({"success": True, "message": "Comment approved"})

@admin_router.post("/comments/{comment_id}/reject")
async def reject_comment(
    comment_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Reject/delete a comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.delete(comment)
    db.commit()
    
    return JSONResponse({"success": True, "message": "Comment deleted"})

@admin_router.post("/comments/{comment_id}/unapprove")
async def unapprove_comment(
    comment_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Unapprove a comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.is_approved = False
    db.commit()
    
    return JSONResponse({"success": True, "message": "Comment unapproved"})

# Include both routers
def get_comments_routers():
    return [router, admin_router]
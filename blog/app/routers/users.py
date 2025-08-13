from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, get_current_user_optional, verify_password, get_password_hash
from app.models.models import User, Post, PostLike, Comment
from typing import Optional

router = APIRouter(tags=["users"])
templates = Jinja2Templates(directory="templates")

@router.get("/profile/{username}", response_class=HTMLResponse)
async def user_profile(
    request: Request,
    username: str,
    db: Session = Depends(get_db)
):
    """Public user profile page"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_user = get_current_user_optional(request, db)
    
    # Get user's published posts
    posts = db.query(Post).filter(
        Post.author_id == user.id,
        Post.is_published == True
    ).order_by(Post.created_at.desc()).limit(10).all()
    
    # Get user stats
    total_posts = db.query(Post).filter(
        Post.author_id == user.id,
        Post.is_published == True
    ).count()
    
    total_comments = db.query(Comment).filter(
        Comment.user_id == user.id,
        Comment.is_approved == True
    ).count()
    
    total_likes = db.query(PostLike).join(Post).filter(
        Post.author_id == user.id
    ).count()
    
    return templates.TemplateResponse("blog/profile.html", {
        "request": request,
        "current_user": current_user,
        "profile_user": user,
        "posts": posts,
        "stats": {
            "total_posts": total_posts,
            "total_comments": total_comments,
            "total_likes": total_likes
        }
    })

@router.get("/profile", response_class=HTMLResponse)
async def my_profile(request: Request, current_user: User = Depends(get_current_user)):
    """Current user's profile settings"""
    return RedirectResponse(url=f"/profile/{current_user.username}")

@router.get("/settings", response_class=HTMLResponse)
async def profile_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User profile settings page"""
    
    # Get available profile images (predefined set)
    available_images = [
        "/static/images/avatars/avatar1.svg",
        "/static/images/avatars/avatar2.svg",
        "/static/images/avatars/avatar3.svg",
        "/static/images/avatars/avatar4.svg",
        "/static/images/avatars/avatar5.svg",
        "/static/images/avatars/avatar6.svg"
    ]
    
    return templates.TemplateResponse("blog/profile_settings.html", {
        "request": request,
        "current_user": current_user,
        "available_images": available_images
    })

@router.post("/settings")
async def update_profile_settings(
    request: Request,
    profile_image: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile settings"""
    
    # Update profile image
    if profile_image:
        current_user.profile_image = profile_image
    
    db.commit()
    
    return RedirectResponse(url="/settings?success=1", status_code=303)

@router.post("/settings/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        return templates.TemplateResponse("blog/profile_settings.html", {
            "request": request,
            "current_user": current_user,
            "error": "Mevcut şifreniz yanlış",
            "available_images": []
        })
    
    # Check password confirmation
    if new_password != confirm_password:
        return templates.TemplateResponse("blog/profile_settings.html", {
            "request": request,
            "current_user": current_user,
            "error": "Yeni şifreler eşleşmiyor",
            "available_images": []
        })
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return RedirectResponse(url="/settings?password_changed=1", status_code=303)

# Like system endpoints
@router.post("/api/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Like or unlike a post"""
    
    post = db.query(Post).filter(Post.id == post_id, Post.is_published == True).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if already liked
    existing_like = db.query(PostLike).filter(
        PostLike.user_id == current_user.id,
        PostLike.post_id == post_id
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        db.commit()
        liked = False
    else:
        # Like
        new_like = PostLike(user_id=current_user.id, post_id=post_id)
        db.add(new_like)
        db.commit()
        liked = True
    
    # Get updated like count
    like_count = db.query(PostLike).filter(PostLike.post_id == post_id).count()
    
    return JSONResponse({
        "success": True,
        "liked": liked,
        "like_count": like_count
    })

@router.get("/api/posts/{post_id}/like-status")
async def get_like_status(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current like status for a post"""
    
    liked = db.query(PostLike).filter(
        PostLike.user_id == current_user.id,
        PostLike.post_id == post_id
    ).first() is not None
    
    like_count = db.query(PostLike).filter(PostLike.post_id == post_id).count()
    
    return JSONResponse({
        "liked": liked,
        "like_count": like_count
    })
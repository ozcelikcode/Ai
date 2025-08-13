from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.models import models
from app.routers import auth, blog, admin, media, users
from app.routers.comments import get_comments_routers
from app.routers.search import get_search_routers
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Blog", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from app.core.templates import templates

# Global template context processor
@app.middleware("http")
async def add_site_settings_to_templates(request, call_next):
    """Add site settings to all template contexts"""
    response = await call_next(request)
    return response

# TemplateResponse override ve filtreler app.core.templates içinde yönetilir

# Router include order matters. Register admin-related routers BEFORE the
# blog router that exposes a catch-all path like `/{slug}` to prevent
# unintended matches such as `/admin` being treated as a page slug.
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(media.router)
app.include_router(users.router)
app.include_router(blog.router)

# Include comment routers
comment_routers = get_comments_routers()
for router in comment_routers:
    app.include_router(router)

# Include search routers
search_routers = get_search_routers()
for router in search_routers:
    app.include_router(router)

from app.core.auth import get_current_user_optional, get_admin_user

def get_template_context(request: Request, db: Session, current_user=None):
    """Get common template context including site settings"""
    site_settings = db.query(models.Settings).first()
    context = {
        "request": request,
        "site_settings": site_settings
    }
    if current_user is not None:
        context["current_user"] = current_user
    return context

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db: Session = Depends(get_db)):
    posts = db.query(models.Post).filter(models.Post.is_published == True).order_by(models.Post.created_at.desc()).limit(10).all()
    current_user = get_current_user_optional(request, db)
    context = get_template_context(request, db, current_user)
    context["posts"] = posts
    return templates.TemplateResponse("blog/index.html", context)



# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
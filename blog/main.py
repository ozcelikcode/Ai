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
from app.utils.ai_content import ai_generator  # Ensure AI is initialized at startup
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Blog", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

# Jinja2 filter'ları ekle
from app.utils.helpers import strip_html_tags, get_excerpt, format_datetime_for_site
import json

templates.env.filters['strip_html'] = strip_html_tags
templates.env.filters['excerpt'] = get_excerpt
templates.env.filters['from_json'] = lambda x: json.loads(x) if x else []
# Timezone filter - requires database session, will be handled in templates

# Global template context processor - simplified
@app.middleware("http")
async def add_site_settings_to_templates(request, call_next):
    """Add site settings to all template contexts"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Middleware error: {e}")
        raise

# Override TemplateResponse to include site settings
original_template_response = templates.TemplateResponse

def template_response_with_settings(name: str, context: dict, status_code: int = 200, **kwargs):
    # Add site settings if not already present and if db session available
    if "site_settings" not in context and "request" in context:
        try:
            from app.core.database import SessionLocal
            from app.models.models import Settings
            db = SessionLocal()
            try:
                context["site_settings"] = db.query(Settings).first()
            except Exception as e:
                print(f"Error loading site settings: {e}")
                context["site_settings"] = None
            finally:
                db.close()
        except Exception as e:
            print(f"Database connection error: {e}")
            context["site_settings"] = None
    
    return original_template_response(name, context, status_code=status_code, **kwargs)

templates.TemplateResponse = template_response_with_settings

# Router include order matters. Register admin-related routers BEFORE the
# blog router that exposes a catch-all path like `/{slug}` to prevent
# unintended matches such as `/admin` being treated as a page slug.
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(media.router)
app.include_router(users.router)

# Include search routers BEFORE blog router (important for /search route)
search_routers = get_search_routers()
for router in search_routers:
    app.include_router(router)

# Include comment routers
comment_routers = get_comments_routers()
for router in comment_routers:
    app.include_router(router)

# Blog router MUST be last due to catch-all /{slug} route
app.include_router(blog.router)

from app.core.auth import get_current_user_optional, get_admin_user
from app.core.database import SessionLocal

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
    db = SessionLocal()
    try:
        current_user = get_current_user_optional(request, db)
        context = get_template_context(request, db, current_user)
        return templates.TemplateResponse("404.html", context, status_code=404)
    except Exception:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    finally:
        db.close()

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    db = SessionLocal()
    try:
        current_user = get_current_user_optional(request, db)
        context = get_template_context(request, db, current_user)
        return templates.TemplateResponse("500.html", context, status_code=500)
    except Exception:
        return templates.TemplateResponse("500.html", {"request": request}, status_code=500)
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("blog/login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        from app.models.models import Settings
        site_settings = db.query(Settings).first()
        return templates.TemplateResponse("blog/login.html", {
            "request": request, 
            "site_settings": site_settings,
            "error": "Invalid username or password"
        })
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/admin" if user.is_admin else "/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    from app.models.models import Settings
    site_settings = db.query(Settings).first()
    return templates.TemplateResponse("blog/register.html", {
        "request": request,
        "site_settings": site_settings
    })

@router.post("/register")
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), password_confirm: str = Form(...), db: Session = Depends(get_db)):
    from app.models.models import Settings
    site_settings = db.query(Settings).first()
    
    if password != password_confirm:
        return templates.TemplateResponse("blog/register.html", {
            "request": request, 
            "site_settings": site_settings,
            "error": "Passwords don't match"
        })
    
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("blog/register.html", {
            "request": request, 
            "site_settings": site_settings,
            "error": "Username already exists"
        })
    
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("blog/register.html", {
            "request": request, 
            "site_settings": site_settings,
            "error": "Email already exists"
        })
    
    hashed_password = get_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    
    return templates.TemplateResponse("blog/login.html", {
        "request": request, 
        "site_settings": site_settings,
        "success": "Account created successfully. Please login."
    })

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response
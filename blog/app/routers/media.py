from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_admin_user
from app.models.models import Media, User
from app.utils.helpers import format_file_size
from app.utils.image_optimizer import optimize_uploaded_image, PRESETS
import os
import uuid
import shutil
from pathlib import Path
from typing import List
import mimetypes
import io

router = APIRouter(prefix="/admin", tags=["media"])
templates = Jinja2Templates(directory="templates")

# Allowed file extensions and max size
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.pdf', '.doc', '.docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.get("/media", response_class=HTMLResponse)
async def media_gallery(request: Request, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    media_files = db.query(Media).order_by(Media.created_at.desc()).all()
    return templates.TemplateResponse("admin/media.html", {
        "request": request,
        "admin_user": admin_user,
        "media_files": media_files
    })

@router.post("/media/upload")
async def upload_media(
    request: Request,
    files: List[UploadFile] = File(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    uploaded_files = []
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/media")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        try:
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                continue
            
            # Validate file size
            file_content = await file.read()
            if len(file_content) > MAX_FILE_SIZE:
                continue
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file.filename)
            if not mime_type:
                mime_type = "application/octet-stream"
            
            # Resim optimizasyonu (sadece resimler için)
            processed_content = file_content
            processed_ext = file_ext
            
            if mime_type.startswith('image/') and file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    # Resmi optimize et
                    optimized_bytes, new_ext = optimize_uploaded_image(
                        file_content, 
                        file.filename,
                        max_width=1920,  # Medium-large boyut
                        max_height=1080,
                        quality=85
                    )
                    processed_content = optimized_bytes
                    processed_ext = new_ext
                    
                    # Optimize edilmiş MIME type
                    if new_ext == '.jpg':
                        mime_type = 'image/jpeg'
                    elif new_ext == '.png':
                        mime_type = 'image/png'
                    elif new_ext == '.webp':
                        mime_type = 'image/webp'
                        
                    print(f"Resim optimize edildi: {len(file_content)} -> {len(processed_content)} bytes")
                    
                except Exception as opt_error:
                    print(f"Resim optimizasyon hatası: {opt_error}")
                    # Optimizasyon başarısızsa orijinal dosyayı kullan
                    processed_content = file_content
                    processed_ext = file_ext
            
            # Generate unique filename with processed extension
            unique_filename = f"{uuid.uuid4()}{processed_ext}"
            file_path = upload_dir / unique_filename
            
            # Save processed file
            with open(file_path, "wb") as buffer:
                buffer.write(processed_content)
            
            # Save to database
            media = Media(
                filename=unique_filename,
                original_name=file.filename,
                file_path=str(file_path),
                file_size=len(processed_content),  # Processed size
                mime_type=mime_type
            )
            
            db.add(media)
            db.commit()
            
            uploaded_files.append({
                "id": media.id,
                "filename": media.filename,
                "original_name": media.original_name,
                "file_size": format_file_size(media.file_size),
                "url": f"/uploads/media/{unique_filename}"
            })
            
        except Exception as e:
            continue
    
    return JSONResponse({
        "success": True,
        "files": uploaded_files
    })

@router.post("/media/upload-url")
async def upload_from_url(
    request: Request,
    url: str = Form(...),
    alt_text: str = Form(""),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    import requests
    from urllib.parse import urlparse
    
    try:
        # Download file from URL
        response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Get file extension from URL
        parsed_url = urlparse(url)
        file_ext = Path(parsed_url.path).suffix.lower()
        if not file_ext:
            # Try to get from content-type
            content_type = response.headers.get('content-type', '')
            if 'image/jpeg' in content_type:
                file_ext = '.jpg'
            elif 'image/png' in content_type:
                file_ext = '.png'
            elif 'image/gif' in content_type:
                file_ext = '.gif'
            else:
                file_ext = '.jpg'  # default
        
        if file_ext not in ALLOWED_EXTENSIONS:
            return JSONResponse({"success": False, "error": "Desteklenmeyen dosya türü"})
        
        # Create uploads directory
        upload_dir = Path("uploads/media")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Download file to memory first
        downloaded_chunks = []
        total_size = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                downloaded_chunks.append(chunk)
                total_size += len(chunk)
                
                # Check file size limit
                if total_size > MAX_FILE_SIZE:
                    return JSONResponse({"success": False, "error": "Dosya çok büyük"})
        
        # Combine chunks
        file_content = b''.join(downloaded_chunks)
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Resim optimizasyonu (sadece resimler için)
        processed_content = file_content
        processed_ext = file_ext
        
        if mime_type.startswith('image/') and file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
            try:
                # URL'den indirilen resmi optimize et
                optimized_bytes, new_ext = optimize_uploaded_image(
                    file_content, 
                    f"downloaded{file_ext}",
                    max_width=1920,
                    max_height=1080,
                    quality=85
                )
                processed_content = optimized_bytes
                processed_ext = new_ext
                
                # Update MIME type
                if new_ext == '.jpg':
                    mime_type = 'image/jpeg'
                elif new_ext == '.png':
                    mime_type = 'image/png'
                elif new_ext == '.webp':
                    mime_type = 'image/webp'
                
                print(f"URL resmi optimize edildi: {len(file_content)} -> {len(processed_content)} bytes")
                
                # Update filename with new extension
                unique_filename = f"{uuid.uuid4()}{processed_ext}"
                file_path = upload_dir / unique_filename
                
            except Exception as opt_error:
                print(f"URL resim optimizasyon hatası: {opt_error}")
                # Optimizasyon başarısızsa orijinal dosyayı kullan
                processed_content = file_content
        
        # Save processed file
        with open(file_path, "wb") as f:
            f.write(processed_content)
        
        file_size = len(processed_content)
        
        # Save to database
        original_name = Path(parsed_url.path).name or "downloaded_file"
        media = Media(
            filename=unique_filename,
            original_name=original_name,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=mime_type,
            alt_text=alt_text
        )
        
        db.add(media)
        db.commit()
        
        return JSONResponse({
            "success": True,
            "file": {
                "id": media.id,
                "filename": media.filename,
                "original_name": media.original_name,
                "file_size": format_file_size(media.file_size),
                "url": f"/uploads/media/{unique_filename}",
                "alt_text": alt_text
            }
        })
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@router.post("/media/{media_id}/update")
async def update_media(
    media_id: int,
    alt_text: str = Form(""),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    media.alt_text = alt_text
    db.commit()
    
    return JSONResponse({"success": True})

@router.post("/media/{media_id}/delete")
async def delete_media(
    media_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Delete file from filesystem
    try:
        if os.path.exists(media.file_path):
            os.unlink(media.file_path)
    except:
        pass
    
    # Delete from database
    db.delete(media)
    db.commit()
    
    return JSONResponse({"success": True})

@router.get("/media/api")
async def get_media_api(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * per_page
    media_files = db.query(Media).order_by(Media.created_at.desc()).offset(offset).limit(per_page).all()
    
    return JSONResponse({
        "media": [{
            "id": media.id,
            "filename": media.filename,
            "original_name": media.original_name,
            "url": f"/uploads/media/{media.filename}",
            "file_size": format_file_size(media.file_size),
            "alt_text": media.alt_text or "",
            "mime_type": media.mime_type,
            "created_at": media.created_at.isoformat()
        } for media in media_files]
    })
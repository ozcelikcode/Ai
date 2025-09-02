from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_admin_user
from app.models.models import Media, User, MediaFolder
from app.utils.helpers import format_file_size, format_datetime_for_site, calculate_file_hash, check_duplicate_media
from app.utils.image_optimizer import optimize_uploaded_image, PRESETS
import os
import uuid
import shutil
from pathlib import Path
from typing import List
import mimetypes
import io
from PIL import Image

router = APIRouter(prefix="/admin", tags=["media"])
templates = Jinja2Templates(directory="templates")

# Allowed file extensions and max size
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.heic', '.heif', '.bmp', '.tiff', '.svg', '.pdf', '.doc', '.docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.get("/media", response_class=HTMLResponse)
async def media_gallery(request: Request, folder_id: int = None, admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    # Get current folder info
    current_folder = None
    if folder_id:
        current_folder = db.query(MediaFolder).filter(MediaFolder.id == folder_id).first()
        if not current_folder:
            folder_id = None  # Invalid folder ID, reset to root
    
    # Get folders in current location
    if folder_id:
        # Get subfolders (if we implement nested folders later)
        folders_in_current = []
        # Get media files in current folder
        all_media_files = db.query(Media).filter(Media.folder_id == folder_id).order_by(Media.created_at.desc()).all()
    else:
        # Get root level folders and unassigned media files
        folders_in_current = db.query(MediaFolder).order_by(MediaFolder.name).all()
        all_media_files = db.query(Media).filter(Media.folder_id == None).order_by(Media.created_at.desc()).all()
    
    # Filter out media files that don't exist on filesystem
    media_files = []
    for media in all_media_files:
        if os.path.exists(media.file_path):
            media_files.append(media)
        else:
            # File doesn't exist, optionally remove from database
            # For now, we just skip showing it
            continue
    
    # Get all folders for sidebar/operations
    all_folders = db.query(MediaFolder).order_by(MediaFolder.name).all()
    
    # Calculate statistics
    total_files = len(media_files)
    total_size = sum(media.file_size for media in media_files)
    image_files = len([media for media in media_files if media.mime_type.startswith('image/')])
    other_files = total_files - image_files
    
    # Convert total size to readable format
    def format_file_size(size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    total_size_formatted = format_file_size(total_size)
    
    # Calculate folder statistics for folders in current view
    for folder in folders_in_current:
        folder.file_count = db.query(Media).filter(Media.folder_id == folder.id).count()
        folder.total_size = sum(media.file_size for media in db.query(Media).filter(Media.folder_id == folder.id).all())
        folder.total_size_formatted = format_file_size(folder.total_size)
    
    # Calculate statistics for all folders (for sidebar)
    for folder in all_folders:
        folder.file_count = db.query(Media).filter(Media.folder_id == folder.id).count()
        folder.total_size = sum(media.file_size for media in db.query(Media).filter(Media.folder_id == folder.id).all())
        folder.total_size_formatted = format_file_size(folder.total_size)
    
    return templates.TemplateResponse("admin/media.html", {
        "request": request,
        "admin_user": admin_user,
        "media_files": media_files,
        "folders_in_current": folders_in_current,
        "all_folders": all_folders,
        "current_folder": current_folder,
        "folder_id": folder_id,
        "format_datetime": lambda dt, fmt="%d.%m.%Y %H:%M": format_datetime_for_site(dt, db, fmt) if dt else "",
        "stats": {
            "total_files": total_files,
            "total_size": total_size_formatted,
            "image_files": image_files,
            "other_files": other_files
        }
    })

@router.post("/media/check-duplicate")
async def check_duplicate(
    request: Request,
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Check if uploaded file is a duplicate"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Calculate hash
        file_hash = calculate_file_hash(file_content)
        file_size = len(file_content)
        
        # Check for duplicate
        duplicate = check_duplicate_media(file_hash, file_size, db)
        
        if duplicate:
            return JSONResponse({
                "is_duplicate": True,
                "duplicate_file": {
                    "id": duplicate.id,
                    "filename": duplicate.filename,
                    "original_name": duplicate.original_name,
                    "title": duplicate.title or duplicate.original_name,
                    "file_size": format_file_size(duplicate.file_size),
                    "url": f"/uploads/media/{duplicate.filename}",
                    "created_at": duplicate.created_at.strftime('%d.%m.%Y %H:%M') if duplicate.created_at else ""
                }
            })
        else:
            return JSONResponse({
                "is_duplicate": False,
                "file_hash": file_hash,
                "file_size": file_size
            })
            
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@router.post("/media/upload")
async def upload_media(
    request: Request,
    files: List[UploadFile] = File(...),
    folder_id: int = Form(None),
    force_upload: bool = Form(False),  # Force upload even if duplicate
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
                
            # Extract image metadata if it's an image
            image_width, image_height = None, None
            if mime_type.startswith('image/'):
                try:
                    with Image.open(io.BytesIO(file_content)) as img:
                        image_width, image_height = img.size
                except Exception:
                    pass
                    
            # Generate title from filename
            auto_title = Path(file.filename).stem.replace('-', ' ').replace('_', ' ').title()
            
            # Calculate file hash for duplicate detection
            file_hash = calculate_file_hash(file_content)
            
            # Check for duplicate if not force upload
            if not force_upload:
                duplicate = check_duplicate_media(file_hash, len(file_content), db)
                if duplicate:
                    # Skip duplicate file
                    continue
            
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
            
            # Recalculate hash for processed content (in case image was optimized)
            final_file_hash = calculate_file_hash(processed_content)
            
            # Save to database
            media = Media(
                filename=unique_filename,
                original_name=file.filename,
                title=auto_title,
                file_path=str(file_path),
                file_size=len(processed_content),  # Processed size
                mime_type=mime_type,
                width=image_width,
                height=image_height,
                file_hash=final_file_hash,
                folder_id=folder_id if folder_id else None
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
            
        # Extract image metadata if it's an image
        image_width, image_height = None, None
        if mime_type.startswith('image/'):
            try:
                with Image.open(io.BytesIO(file_content)) as img:
                    image_width, image_height = img.size
            except Exception:
                pass
                
        # Generate title from URL filename
        auto_title = Path(parsed_url.path).stem.replace('-', ' ').replace('_', ' ').title()
        if not auto_title or auto_title == '':
            auto_title = "Downloaded Image"
        
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
        
        # Calculate hash for processed content
        final_file_hash = calculate_file_hash(processed_content)
        
        # Save to database
        original_name = Path(parsed_url.path).name or "downloaded_file"
        media = Media(
            filename=unique_filename,
            original_name=original_name,
            title=auto_title,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=mime_type,
            width=image_width,
            height=image_height,
            file_hash=final_file_hash,
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
    title: str = Form(""),
    description: str = Form(""),
    alt_text: str = Form(""),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    media.title = title if title else None
    media.description = description if description else None
    media.alt_text = alt_text if alt_text else None
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

@router.post("/media/bulk-delete")
async def bulk_delete_media(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        media_ids = data.get('media_ids', [])
        
        if not media_ids:
            return JSONResponse({"success": False, "error": "No media selected"})
        
        # Get media files to delete
        media_files = db.query(Media).filter(Media.id.in_(media_ids)).all()
        
        # Delete files from filesystem
        for media in media_files:
            try:
                if os.path.exists(media.file_path):
                    os.unlink(media.file_path)
            except:
                pass
        
        # Delete from database
        db.query(Media).filter(Media.id.in_(media_ids)).delete(synchronize_session=False)
        db.commit()
        
        return JSONResponse({"success": True, "deleted_count": len(media_files)})
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@router.get("/media/search")
async def search_media(
    request: Request,
    q: str = "",
    folder_id: int = None,
    page: int = 1,
    per_page: int = 20,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Search media files and folders by title, filename, description, alt_text, folder name"""
    try:
        print(f"Search request - q: '{q}', folder_id: '{folder_id}', page: {page}, per_page: {per_page}")
        from sqlalchemy import or_, and_
        
        # If no search query, return current folder contents
        if not q or not q.strip():
            # Base query for media files
            query = db.query(Media)
            
            # Apply folder filter if specified
            if folder_id is not None:
                query = query.filter(Media.folder_id == folder_id)
            else:
                query = query.filter(Media.folder_id == None)
            
            # Get folders in current location (for empty search)
            if folder_id is None:
                folders_in_current = db.query(MediaFolder).order_by(MediaFolder.name).all()
            else:
                folders_in_current = []  # Nested folders not implemented yet
            
            # Apply pagination and ordering for media files
            offset = (page - 1) * per_page
            all_media_files = query.order_by(Media.created_at.desc()).offset(offset).limit(per_page).all()
            
            # Filter out media files that don't exist on filesystem
            media_files = []
            for media in all_media_files:
                if os.path.exists(media.file_path):
                    media_files.append(media)
                    
            return JSONResponse({
                "media": [{
                    "id": media.id,
                    "filename": media.filename,
                    "original_name": media.original_name,
                    "title": media.title or "",
                    "description": media.description or "",
                    "url": f"/uploads/media/{media.filename}",
                    "file_size": format_file_size(media.file_size),
                    "alt_text": media.alt_text or "",
                    "mime_type": media.mime_type,
                    "width": media.width or 0,
                    "height": media.height or 0,
                    "created_at": format_datetime_for_site(media.created_at, db) if media.created_at else "",
                    "type": "media"
                } for media in media_files],
                "folders": [{
                    "id": folder.id,
                    "name": folder.name,
                    "description": folder.description or "",
                    "color": folder.color,
                    "file_count": db.query(Media).filter(Media.folder_id == folder.id).count(),
                    "created_at": format_datetime_for_site(folder.created_at, db) if folder.created_at else "",
                    "type": "folder"
                } for folder in folders_in_current],
                "total": len(media_files) + len(folders_in_current),
                "page": page,
                "per_page": per_page,
                "has_more": len(media_files) == per_page
            })
        
        # Search both media files and folders when query is provided
        search_term = f"%{q.strip()}%"
        
        # Search media files
        media_query = db.query(Media)
        if folder_id is not None:
            media_query = media_query.filter(Media.folder_id == folder_id)
        
        media_query = media_query.filter(
            or_(
                Media.title.ilike(search_term),
                Media.original_name.ilike(search_term),
                Media.description.ilike(search_term),
                Media.alt_text.ilike(search_term),
                Media.mime_type.ilike(search_term)
            )
        )
        
        # Search folders (only if not inside a specific folder or search across all)
        folders_query = db.query(MediaFolder)
        if not folder_id:  # Search all folders when in root
            folders_query = folders_query.filter(
                or_(
                    MediaFolder.name.ilike(search_term),
                    MediaFolder.description.ilike(search_term)
                )
            )
        else:
            # When inside a folder, don't show other folders in search results
            folders_query = folders_query.filter(MediaFolder.id == -1)  # No results
        
        # Get results
        all_media_files = media_query.order_by(Media.created_at.desc()).all()
        matching_folders = folders_query.order_by(MediaFolder.name).all()
        
        # Filter out media files that don't exist on filesystem
        media_files = []
        for media in all_media_files:
            if os.path.exists(media.file_path):
                media_files.append(media)
        
        # Calculate folder statistics
        for folder in matching_folders:
            folder.file_count = db.query(Media).filter(Media.folder_id == folder.id).count()
        
        print(f"Search found {len(media_files)} media files, {len(matching_folders)} folders")
        
        # Combine results
        all_results = []
        
        # Add folders first
        for folder in matching_folders:
            all_results.append({
                "id": folder.id,
                "name": folder.name,
                "description": folder.description or "",
                "color": folder.color,
                "file_count": folder.file_count,
                "created_at": format_datetime_for_site(folder.created_at, db) if folder.created_at else "",
                "type": "folder"
            })
        
        # Add media files
        for media in media_files:
            all_results.append({
                "id": media.id,
                "filename": media.filename,
                "original_name": media.original_name,
                "title": media.title or "",
                "description": media.description or "",
                "url": f"/uploads/media/{media.filename}",
                "file_size": format_file_size(media.file_size),
                "alt_text": media.alt_text or "",
                "mime_type": media.mime_type,
                "width": media.width or 0,
                "height": media.height or 0,
                "created_at": format_datetime_for_site(media.created_at, db) if media.created_at else "",
                "type": "media"
            })
        
        # Apply pagination to combined results
        offset = (page - 1) * per_page
        paginated_results = all_results[offset:offset + per_page]
        
        return JSONResponse({
            "results": paginated_results,
            "total": len(all_results),
            "page": page,
            "per_page": per_page,
            "has_more": len(all_results) > (page * per_page)
        })
        
    except Exception as e:
        print(f"Search error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "media": [],
            "total": 0,
            "page": 1,
            "per_page": per_page,
            "has_more": False
        })

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
            "title": media.title or "",
            "description": media.description or "",
            "url": f"/uploads/media/{media.filename}",
            "file_size": format_file_size(media.file_size),
            "alt_text": media.alt_text or "",
            "mime_type": media.mime_type,
            "created_at": media.created_at.isoformat()
        } for media in media_files]
    })

# Folder Management Routes
@router.post("/media/folders/create")
async def create_folder(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    color: str = Form("#944f37"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new media folder"""
    
    # Check if folder name already exists
    existing_folder = db.query(MediaFolder).filter(MediaFolder.name == name).first()
    if existing_folder:
        return JSONResponse({"success": False, "error": "Bu isimde bir klasör zaten mevcut"})
    
    folder = MediaFolder(
        name=name,
        description=description,
        color=color
    )
    
    db.add(folder)
    db.commit()
    
    return JSONResponse({"success": True, "folder_id": folder.id})

@router.post("/media/folders/{folder_id}/update")
async def update_folder(
    folder_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    color: str = Form("#944f37"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update a media folder"""
    
    folder = db.query(MediaFolder).filter(MediaFolder.id == folder_id).first()
    if not folder:
        return JSONResponse({"success": False, "error": "Klasör bulunamadı"})
    
    # Check if name is taken by another folder
    existing_folder = db.query(MediaFolder).filter(
        MediaFolder.name == name, 
        MediaFolder.id != folder_id
    ).first()
    if existing_folder:
        return JSONResponse({"success": False, "error": "Bu isimde bir klasör zaten mevcut"})
    
    folder.name = name
    folder.description = description
    folder.color = color
    db.commit()
    
    return JSONResponse({"success": True})

@router.post("/media/folders/{folder_id}/delete")
async def delete_folder(
    folder_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a media folder"""
    
    folder = db.query(MediaFolder).filter(MediaFolder.id == folder_id).first()
    if not folder:
        return JSONResponse({"success": False, "error": "Klasör bulunamadı"})
    
    # Move all files in this folder to no folder (null)
    db.query(Media).filter(Media.folder_id == folder_id).update({"folder_id": None})
    
    # Delete the folder
    db.delete(folder)
    db.commit()
    
    return JSONResponse({"success": True})

@router.post("/media/{media_id}/move")
async def move_media_to_folder(
    media_id: int,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Move media file to a folder"""
    
    try:
        data = await request.json()
        folder_id = data.get('folder_id')  # None for root folder
        
        media = db.query(Media).filter(Media.id == media_id).first()
        if not media:
            return JSONResponse({"success": False, "error": "Dosya bulunamadı"})
        
        if folder_id:
            folder = db.query(MediaFolder).filter(MediaFolder.id == folder_id).first()
            if not folder:
                return JSONResponse({"success": False, "error": "Klasör bulunamadı"})
        
        media.folder_id = folder_id
        db.commit()
        
        return JSONResponse({"success": True})
        
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
"""Digital Library API routes - Independent from physical books."""
import os
import shutil
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models import User, DigitalBook, BookDigitalLink, Book
from app.auth import get_current_user, get_current_admin_user, get_current_librarian_or_admin, get_current_user_optional
from app.utils import format_subject
from app.schemas import (
    DigitalBookCreate, 
    DigitalBookUpdate, 
    DigitalBookResponse,
    DigitalBookDetailResponse,
    BookDigitalLinkCreate,
    BookDigitalLinkResponse
)

router = APIRouter(prefix="/api/digital-library", tags=["digital-library"])

# Track recent downloads to prevent double-counting (user_id, book_id, timestamp)
_recent_downloads = {}

# Allowed file formats
ALLOWED_FORMATS = ["pdf", "epub", "mobi"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY_VAULT = os.path.join(BASE_DIR, "library_vault", "digital_books")

# Ensure library vault exists
os.makedirs(LIBRARY_VAULT, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove special characters."""
    import re
    # Remove or replace special characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename[:100]  # Limit length


@router.get("", response_model=List[DigitalBookResponse])
async def list_digital_books(
    search: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    file_format: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List all digital books with optional filtering. Public access allowed."""
    query = db.query(DigitalBook)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                DigitalBook.title.ilike(search_pattern),
                DigitalBook.author.ilike(search_pattern),
                DigitalBook.isbn.ilike(search_pattern),
                DigitalBook.description.ilike(search_pattern)
            )
        )
    
    if subject:
        query = query.filter(DigitalBook.subject.ilike(f"%{subject}%"))
    
    if category:
        query = query.filter(DigitalBook.category == category)
    
    if language:
        query = query.filter(DigitalBook.language == language)
    
    if file_format:
        query = query.filter(DigitalBook.file_format == file_format.lower())
    
    digital_books = query.order_by(DigitalBook.created_at.desc()).offset(skip).limit(limit).all()
    return digital_books


@router.get("/{digital_book_id}", response_model=DigitalBookDetailResponse)
async def get_digital_book(
    digital_book_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a specific digital book with details. Public access allowed."""
    digital_book = db.query(DigitalBook).filter(DigitalBook.id == digital_book_id).first()
    if not digital_book:
        raise HTTPException(status_code=404, detail="Digital book not found")
    
    # Get uploader name
    uploader_name = digital_book.uploader.full_name if digital_book.uploader else None
    
    # Get linked physical books
    linked_books = []
    for link in digital_book.physical_links:
        linked_books.append({
            "link_id": link.id,
            "book_id": link.book.id,
            "acc_no": link.book.acc_no,
            "title": link.book.title,
            "author": link.book.author,
            "storage_loc": link.book.storage_loc,
            "is_issued": link.book.is_issued,
            "link_type": link.link_type
        })
    
    # Convert to dict and add extra fields
    result = DigitalBookResponse.model_validate(digital_book).model_dump()
    result["uploader_name"] = uploader_name
    result["linked_physical_books"] = linked_books
    
    return result


@router.post("", response_model=DigitalBookResponse)
async def create_digital_book(
    title: str = Form(...),
    author: str = Form(...),
    file: UploadFile = File(...),
    publisher: Optional[str] = Form(None),
    publication_year: Optional[int] = Form(None),
    isbn: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    language: str = Form("English"),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Upload a new digital book (Librarian/Admin only)."""
    # Validate file format
    file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if file_ext not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_FORMATS)}"
        )
    
    # Create safe filename
    safe_title = sanitize_filename(title)
    filename = f"{safe_title}.{file_ext}"
    
    # Check if file already exists, add counter if needed
    base_path = os.path.join(LIBRARY_VAULT, filename)
    counter = 1
    while os.path.exists(base_path):
        filename = f"{safe_title}_{counter}.{file_ext}"
        base_path = os.path.join(LIBRARY_VAULT, filename)
        counter += 1
    
    # Save file
    try:
        with open(base_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(base_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create database record
    formatted_subject = format_subject(subject) if subject else None
    
    digital_book = DigitalBook(
        title=title,
        author=author,
        file_path=filename,
        file_size=file_size,
        file_format=file_ext,
        publisher=publisher,
        publication_year=publication_year,
        isbn=isbn,
        subject=formatted_subject,
        description=description,
        language=language,
        category=category,
        tags=tags,
        uploaded_by=current_user.id
    )
    
    db.add(digital_book)
    db.commit()
    db.refresh(digital_book)
    
    return digital_book


@router.put("/{digital_book_id}", response_model=DigitalBookResponse)
async def update_digital_book(
    digital_book_id: int,
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    publisher: Optional[str] = Form(None),
    publication_year: Optional[int] = Form(None),
    isbn: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Update digital book metadata (Librarian/Admin only)."""
    digital_book = db.query(DigitalBook).filter(DigitalBook.id == digital_book_id).first()
    if not digital_book:
        raise HTTPException(status_code=404, detail="Digital book not found")
    
    # Update fields
    if title:
        digital_book.title = title
    if author:
        digital_book.author = author
    if publisher is not None:
        digital_book.publisher = publisher
    if publication_year is not None:
        digital_book.publication_year = publication_year
    if isbn is not None:
        digital_book.isbn = isbn
    if subject is not None:
        digital_book.subject = format_subject(subject)
    if description is not None:
        digital_book.description = description
    if language:
        digital_book.language = language
    if category is not None:
        digital_book.category = category
    if tags is not None:
        digital_book.tags = tags
    
    digital_book.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(digital_book)
    
    return digital_book


@router.delete("/{digital_book_id}")
async def delete_digital_book(
    digital_book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a digital book (Admin only)."""
    digital_book = db.query(DigitalBook).filter(DigitalBook.id == digital_book_id).first()
    if not digital_book:
        raise HTTPException(status_code=404, detail="Digital book not found")
    
    # Get physical file path
    # Use os.path.basename to prevent directory traversal or absolute path issues stored in DB
    filename = os.path.basename(digital_book.file_path)
    file_path = os.path.join(LIBRARY_VAULT, filename)
    
    # Also check parent directory as fallback (legacy storage)
    parent_vault = os.path.dirname(LIBRARY_VAULT)
    fallback_path = os.path.join(parent_vault, filename)
    
    # Delete physical file(s)
    deleted_physical = False
    for path in [file_path, fallback_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted_physical = True
            except Exception as e:
                # If we found the file but couldn't delete it, we should report an error
                raise HTTPException(
                    status_code=500, 
                    detail=f"Found file at {path} but failed to delete: {str(e)}"
                )
    
    # Manual cleanup of links since cascade might not be configured in the DB/Model
    db.query(BookDigitalLink).filter(BookDigitalLink.digital_book_id == digital_book_id).delete()
    
    # Delete database record
    db.delete(digital_book)
    db.commit()
    
    msg = "Digital book and file deleted successfully" if deleted_physical else "Digital book record deleted (physical file was already missing)"
    return {"message": msg}


@router.get("/{digital_book_id}/view")
async def view_digital_book(
    digital_book_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """View/stream a digital book file. Public access allowed.
    
    Authentication is optional. If provided via:
    1. Authorization header (standard)
    2. token query parameter (for iframe embedding)
    
    View count incremented regardless of authentication.
    """
    # Try to get user from query parameter token (for iframe)
    from app.auth import get_user_from_token_query
    current_user = await get_user_from_token_query(token, db)
    
    # If no token in query, try standard authentication (optional)
    if not current_user:
        from app.auth import get_current_user_optional
        current_user = await get_current_user_optional(db)
    
    # Continue regardless of authentication (public access)
    
    digital_book = db.query(DigitalBook).filter(DigitalBook.id == digital_book_id).first()
    if not digital_book:
        raise HTTPException(status_code=404, detail="Digital book not found")
    
    # Resolve physical file path
    filename = os.path.basename(digital_book.file_path)
    file_path = os.path.join(LIBRARY_VAULT, filename)
    
    # Check fallback path if not found in primary
    if not os.path.exists(file_path):
        parent_vault = os.path.dirname(LIBRARY_VAULT)
        fallback_path = os.path.join(parent_vault, filename)
        if os.path.exists(fallback_path):
            file_path = fallback_path
        else:
            raise HTTPException(status_code=404, detail="File not found in vault")
    
    # Increment view count
    digital_book.view_count += 1
    db.commit()
    
    # Determine media type
    media_types = {
        "pdf": "application/pdf",
        "epub": "application/epub+zip",
        "mobi": "application/x-mobipocket-ebook"
    }
    media_type = media_types.get(digital_book.file_format, "application/octet-stream")
    
    # For viewing, set Content-Disposition to inline (not attachment)
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={digital_book.file_path}"}
    )


@router.get("/{digital_book_id}/download")
async def download_digital_book(
    digital_book_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Download a digital book file. Public access allowed.
    
    Authentication is optional. If provided via:
    1. Authorization header (standard)
    2. token query parameter (for direct download links)
    
    Download count incremented regardless of authentication.
    """
    # Try to get user from query parameter token
    from app.auth import get_user_from_token_query
    current_user = await get_user_from_token_query(token, db)
    
    # If no token in query, try standard authentication (optional)
    if not current_user:
        from app.auth import get_current_user_optional
        current_user = await get_current_user_optional(db)
    
    # Continue regardless of authentication (public access)
    
    digital_book = db.query(DigitalBook).filter(DigitalBook.id == digital_book_id).first()
    if not digital_book:
        raise HTTPException(status_code=404, detail="Digital book not found")
    
    # Resolve physical file path
    filename = os.path.basename(digital_book.file_path)
    file_path = os.path.join(LIBRARY_VAULT, filename)
    
    # Check fallback path if not found in primary
    if not os.path.exists(file_path):
        parent_vault = os.path.dirname(LIBRARY_VAULT)
        fallback_path = os.path.join(parent_vault, filename)
        if os.path.exists(fallback_path):
            file_path = fallback_path
        else:
            raise HTTPException(status_code=404, detail="File not found in vault")
    
    # Increment download count
    # Use user ID if authenticated, otherwise use IP-based tracking
    user_identifier = str(current_user.id) if current_user else "anonymous"
    download_key = f"{user_identifier}_{digital_book_id}"
    current_time = datetime.utcnow()
    
    # Clean old entries (older than 10 seconds)
    global _recent_downloads
    _recent_downloads = {k: v for k, v in _recent_downloads.items() 
                         if current_time - v < timedelta(seconds=10)}
    
    # Only increment if not a duplicate request
    if download_key not in _recent_downloads or \
       current_time - _recent_downloads[download_key] > timedelta(seconds=5):
        digital_book.download_count += 1
        _recent_downloads[download_key] = current_time
        db.commit()
    
    # Determine media type
    media_types = {
        "pdf": "application/pdf",
        "epub": "application/epub+zip",
        "mobi": "application/x-mobipocket-ebook"
    }
    media_type = media_types.get(digital_book.file_format, "application/octet-stream")
    
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={digital_book.file_path}"},
        filename=digital_book.file_path
    )


@router.get("/stats/overview")
async def get_digital_library_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get digital library statistics."""
    total_books = db.query(DigitalBook).count()
    total_views = db.query(func.sum(DigitalBook.view_count)).scalar() or 0
    total_downloads = db.query(func.sum(DigitalBook.download_count)).scalar() or 0
    
    # Get counts by format
    format_stats = db.query(
        DigitalBook.file_format,
        func.count(DigitalBook.id).label('count')
    ).group_by(DigitalBook.file_format).all()
    
    # Get counts by category
    category_stats = db.query(
        DigitalBook.category,
        func.count(DigitalBook.id).label('count')
    ).filter(
        DigitalBook.category != None,
        DigitalBook.category != ""
    ).group_by(DigitalBook.category).all()
    
    # Get counts by subject
    subject_stats = db.query(
        DigitalBook.subject,
        func.count(DigitalBook.id).label('count')
    ).filter(
        DigitalBook.subject != None,
        DigitalBook.subject != ""
    ).group_by(DigitalBook.subject).order_by(func.count(DigitalBook.id).desc()).limit(10).all()
    
    return {
        "total_books": total_books,
        "total_views": total_views,
        "total_downloads": total_downloads,
        "by_format": [{"format": f[0], "count": f[1]} for f in format_stats],
        "by_category": [{"category": c[0], "count": c[1]} for c in category_stats],
        "top_subjects": [{"subject": s[0], "count": s[1]} for s in subject_stats]
    }


@router.get("/filters/categories")
async def get_categories(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get unique categories for filtering. Public access allowed."""
    categories = db.query(DigitalBook.category).filter(
        DigitalBook.category != None,
        DigitalBook.category != ""
    ).distinct().all()
    return [c[0] for c in categories]


@router.get("/filters/subjects")
async def get_subjects(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get unique subjects for filtering. Public access allowed."""
    subjects = db.query(DigitalBook.subject).filter(
        DigitalBook.subject != None,
        DigitalBook.subject != ""
    ).distinct().all()
    return [s[0] for s in subjects]


@router.get("/filters/languages")
async def get_languages(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get unique languages for filtering. Public access allowed."""
    languages = db.query(DigitalBook.language).distinct().all()
    return [l[0] for l in languages]


# Physical Book Linking Routes
@router.post("/links", response_model=BookDigitalLinkResponse)
async def create_book_link(
    link_data: BookDigitalLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Link a physical book to a digital book (Librarian/Admin only)."""
    # Verify book exists
    book = db.query(Book).filter(Book.id == link_data.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Physical book not found")
    
    # Verify digital book exists
    digital_book = db.query(DigitalBook).filter(DigitalBook.id == link_data.digital_book_id).first()
    if not digital_book:
        raise HTTPException(status_code=404, detail="Digital book not found")
    
    # Check if link already exists
    existing_link = db.query(BookDigitalLink).filter(
        BookDigitalLink.book_id == link_data.book_id,
        BookDigitalLink.digital_book_id == link_data.digital_book_id
    ).first()
    
    if existing_link:
        raise HTTPException(status_code=400, detail="Link already exists")
    
    # Create link
    link = BookDigitalLink(
        book_id=link_data.book_id,
        digital_book_id=link_data.digital_book_id,
        link_type=link_data.link_type,
        notes=link_data.notes
    )
    
    db.add(link)
    db.commit()
    db.refresh(link)
    
    return link


@router.get("/links/{digital_book_id}", response_model=List[BookDigitalLinkResponse])
async def get_digital_book_links(
    digital_book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all physical book links for a digital book."""
    links = db.query(BookDigitalLink).filter(
        BookDigitalLink.digital_book_id == digital_book_id
    ).all()
    return links


@router.delete("/links/{link_id}")
async def delete_book_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a book-digital link (Admin only)."""
    link = db.query(BookDigitalLink).filter(BookDigitalLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    db.delete(link)
    db.commit()
    
    return {"message": "Link deleted successfully"}


@router.get("/search/by-physical-book/{book_id}")
async def find_digital_by_physical(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Find digital books linked to a physical book."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Physical book not found")
    
    # Get linked digital books
    digital_books = []
    for link in book.digital_links:
        digital_books.append({
            "digital_book": DigitalBookResponse.model_validate(link.digital_book).model_dump(),
            "link_type": link.link_type,
            "link_id": link.id
        })
    
    return digital_books

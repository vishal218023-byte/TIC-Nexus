"""Main FastAPI application for TIC Nexus."""
import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.database import engine, get_db, Base
from app.models import User, Book, Transaction, DigitalBook, BookDigitalLink
from app.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    get_current_user,
    get_current_admin_user
)
from app.schemas import (
    UserCreate, UserResponse, BookCreate, BookUpdate, BookResponse,
    Token, DashboardStats, SubjectDistribution
)
from app.circulation import issue_book, retrieve_book, extend_book, update_overdue_status
from app.routes import router
from app.digital_library_routes import router as digital_library_router
from app.password_reset import router as password_reset_router

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="TIC Nexus",
    description="Technical Information Center - Bharat Electronics Limited",
    version="1.0.0"
)

# Setup directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY_VAULT = os.path.join(BASE_DIR, "library_vault")
DIGITAL_BOOKS_DIR = os.path.join(LIBRARY_VAULT, "digital_books")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(LIBRARY_VAULT, exist_ok=True)
os.makedirs(DIGITAL_BOOKS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include API routes
app.include_router(router)
app.include_router(digital_library_router)
app.include_router(password_reset_router)


# Initialize default admin user on startup
@app.on_event("startup")
async def startup_event():
    """Create default admin user if none exists."""
    db = next(get_db())
    try:
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count == 0:
            default_admin = User(
                username="admin",
                email="admin@bel.in",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(default_admin)
            db.commit()
            print("✓ Default admin user created (username: admin, password: admin123)")
        
        # Update overdue status on startup
        overdue_count = update_overdue_status(db)
        if overdue_count > 0:
            print(f"✓ Updated {overdue_count} overdue transactions")
    finally:
        db.close()


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    # Handle redirect (303) - redirect to login
    if exc.status_code == status.HTTP_303_SEE_OTHER:
        location = exc.headers.get("Location", "/login")
        return RedirectResponse(url=location, status_code=status.HTTP_303_SEE_OTHER)
    
    if request.url.path.startswith("/api/"):
        # Return JSON for API calls
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    # For web routes, render error page
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error_code": exc.status_code, "error_message": exc.detail},
        status_code=exc.status_code
    )


# Root - Homepage
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render public homepage."""
    return templates.TemplateResponse("home_bulma.html", {"request": request})


# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Render forgot password page."""
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Render reset password with token page."""
    return templates.TemplateResponse("reset_password.html", {"request": request})


@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.role, 
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name
    }


# Dashboard routes - moved to protected section below


@app.get("/api/dashboard/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DashboardStats:
    """Get dashboard statistics."""
    # Update overdue status
    update_overdue_status(db)
    
    total_books = db.query(Book).count()
    total_issued = db.query(Book).filter(Book.is_issued == True).count()
    total_overdue = db.query(Transaction).filter(Transaction.status == "Overdue").count()
    total_users = db.query(User).count()
    digital_library_count = db.query(DigitalBook).count()
    
    return DashboardStats(
        total_books=total_books,
        total_issued=total_issued,
        total_overdue=total_overdue,
        total_users=total_users,
        digital_library_count=digital_library_count
    )


@app.get("/api/dashboard/subject-distribution")
async def get_subject_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[SubjectDistribution]:
    """Get top 10 subject distribution for charts."""
    results = db.query(
        Book.subject,
        func.count(Book.id).label("count")
    ).filter(
        Book.subject != None,
        Book.subject != ""
    ).group_by(Book.subject).order_by(func.count(Book.id).desc()).limit(10).all()
    
    return [SubjectDistribution(subject=r[0] or "Unknown", count=r[1]) for r in results]


# Public API Endpoints (No Authentication Required)
@app.get("/api/public/search")
async def public_search_books(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Public search endpoint for books."""
    search_pattern = f"%{q}%"
    books = db.query(Book).filter(
        or_(
            Book.title.ilike(search_pattern),
            Book.author.ilike(search_pattern),
            Book.acc_no.ilike(search_pattern),
            Book.isbn.ilike(search_pattern)
        )
    ).limit(20).all()
    
    results = []
    for book in books:
        # Check for digital links
        digital_link = db.query(BookDigitalLink).filter(BookDigitalLink.book_id == book.id).first()
        digital_book_id = None
        digital_book_format = None
        
        if digital_link:
            digital_book_id = digital_link.digital_book_id
            # Get format for public linking
            digital_book = db.query(DigitalBook).filter(DigitalBook.id == digital_book_id).first()
            if digital_book:
                digital_book_format = digital_book.file_format
        
        results.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "acc_no": book.acc_no,
            "isbn": book.isbn,
            "subject": book.subject,
            "language": book.language,
            "is_issued": book.is_issued,
            "digital_book_id": digital_book_id,
            "digital_book_format": digital_book_format
        })
    
    return results


@app.get("/api/public/stats")
async def public_stats(db: Session = Depends(get_db)):
    """Public statistics endpoint."""
    total_books = db.query(Book).count()
    available_books = db.query(Book).filter(Book.is_issued == False).count()
    digital_library_count = db.query(DigitalBook).count()
    subjects_count = db.query(Book.subject).filter(
        Book.subject != None,
        Book.subject != ""
    ).distinct().count()
    
    return {
        "total_books": total_books,
        "available_books": available_books,
        "digital_library_count": digital_library_count,
        "subjects_count": subjects_count
    }


# Public Digital Library Route (No Authentication Required)
@app.get("/public/digital-library", response_class=HTMLResponse)
async def public_digital_library_page(request: Request):
    """Render public digital library browse page (no authentication required)."""
    return templates.TemplateResponse("public_digital_library.html", {"request": request})


@app.get("/public/digital-library/view/{book_id}", response_class=HTMLResponse)
async def public_digital_view_page(request: Request, book_id: int, db: Session = Depends(get_db)):
    """Render a public view page for a digital book with the correct title."""
    digital_book = db.query(DigitalBook).filter(DigitalBook.id == book_id).first()
    if not digital_book:
        raise HTTPException(status_code=404, detail="Digital book not found")
    
    return templates.TemplateResponse(
        "public_digital_view.html", 
        {
            "request": request, 
            "book": digital_book,
            "pdf_url": f"/api/digital-library/{book_id}/view"
        }
    )


# Protected Page Routes (Authentication Required - Client-side check)
# Note: These routes serve the HTML. Authentication is checked client-side via JavaScript.
# The actual API endpoints still require proper authentication.
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page_protected(
    request: Request
):
    """Render dashboard page (login required - checked client-side)."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(
    request: Request
):
    """Render inventory page (login required - checked client-side)."""
    return templates.TemplateResponse("inventory.html", {"request": request})


@app.get("/circulation", response_class=HTMLResponse)
async def circulation_page(
    request: Request
):
    """Render circulation page (login required - checked client-side)."""
    return templates.TemplateResponse("circulation.html", {"request": request})


@app.get("/digital-library", response_class=HTMLResponse)
async def digital_library_page(
    request: Request
):
    """Render digital library browse page (login required - checked client-side)."""
    return templates.TemplateResponse("digital_library_browse.html", {"request": request})


@app.get("/digital-library/{book_id}", response_class=HTMLResponse)
async def digital_library_detail_page(
    request: Request,
    book_id: int
):
    """Render digital library detail page (login required - checked client-side)."""
    return templates.TemplateResponse("digital_library_detail.html", {"request": request})


@app.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request
):
    """Render user management page (login required - checked client-side)."""
    return templates.TemplateResponse("users.html", {"request": request})



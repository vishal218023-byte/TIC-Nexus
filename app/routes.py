"""Additional API routes for books, circulation, and digital library."""
import os
import shutil
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import User, Book, Transaction, BookDigitalLink
from app.auth import get_current_user, get_current_admin_user, get_current_librarian_or_admin
from app.schemas import BookCreate, BookUpdate, BookResponse, TransactionResponse
from app.circulation import issue_book, retrieve_book, extend_book

router = APIRouter(prefix="/api")

# Book Management Routes
@router.get("/books", response_model=List[BookResponse])
async def list_books(
    search: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    is_issued: Optional[bool] = Query(None),
    language: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all books with optional filtering."""
    query = db.query(Book)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Book.title.ilike(search_pattern),
                Book.author.ilike(search_pattern),
                Book.acc_no.ilike(search_pattern),
                Book.isbn.ilike(search_pattern)
            )
        )
    
    if subject:
        query = query.filter(Book.subject == subject)
    
    if language:
        query = query.filter(Book.language == language)
    
    if is_issued is not None:
        query = query.filter(Book.is_issued == is_issued)
    
    books = query.offset(skip).limit(limit).all()
    
    # Populate digital_book_id for each book
    for book in books:
        link = db.query(BookDigitalLink).filter(BookDigitalLink.book_id == book.id).first()
        book.digital_book_id = link.digital_book_id if link else None
        
    return books


@router.get("/languages")
async def list_languages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unique languages for filtering."""
    languages = db.query(Book.language).filter(
        Book.language != None,
        Book.language != ""
    ).distinct().all()
    return [l[0] for l in languages]


@router.get("/books/available")
async def list_available_books(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Get all books with availability status for issuing (Librarian/Admin only)."""
    # Query all books, not just available ones
    query = db.query(Book)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Book.acc_no.ilike(search_pattern),
                Book.title.ilike(search_pattern),
                Book.author.ilike(search_pattern)
            )
        )
    
    books = query.offset(skip).limit(limit).all()
    
    # Build response with availability status
    result = []
    for book in books:
        # Check for digital links
        link = db.query(BookDigitalLink).filter(BookDigitalLink.book_id == book.id).first()
        digital_book_id = link.digital_book_id if link else None
        
        result.append({
            "id": book.id,
            "acc_no": book.acc_no,
            "title": book.title,
            "author": book.author,
            "subject": book.subject,
            "class_no": book.class_no,
            "year": book.year,
            "isbn": book.isbn,
            "storage_loc": book.storage_loc,
            "is_issued": book.is_issued,
            "can_issue": not book.is_issued,
            "digital_book_id": digital_book_id,
            "created_at": book.created_at.isoformat(),
            "updated_at": book.updated_at.isoformat()
        })
    
    return result


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific book by ID."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Populate digital_book_id
    link = db.query(BookDigitalLink).filter(BookDigitalLink.book_id == book.id).first()
    book.digital_book_id = link.digital_book_id if link else None
    
    return book


@router.post("/books", response_model=BookResponse)
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Create a new book (Librarian/Admin only)."""
    # Check if accession number already exists
    existing = db.query(Book).filter(Book.acc_no == book.acc_no).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Book with accession number {book.acc_no} already exists"
        )
    
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@router.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a book (Admin only)."""
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    update_data = book_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    
    db_book.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_book)
    return db_book


@router.delete("/books/{book_id}")
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a book (Admin only)."""
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if db_book.is_issued:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a book that is currently issued"
        )
    
    db.delete(db_book)
    db.commit()
    return {"message": "Book deleted successfully"}


# Circulation Routes
@router.post("/circulation/issue")
async def issue_book_route(
    book_id: int = Form(...),
    user_id: int = Form(...),
    days: int = Form(14, ge=1, le=90),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Issue a book to a user (Librarian/Admin only)."""
    due_date = datetime.utcnow() + timedelta(days=days)
    transaction = issue_book(db, book_id, user_id, due_date, notes)
    return {"message": "Book issued successfully", "transaction_id": transaction.id}


@router.post("/circulation/return")
async def return_book_route(
    transaction_id: int = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Return a book (Librarian/Admin only)."""
    transaction = retrieve_book(db, transaction_id, notes)
    return {"message": "Book returned successfully", "transaction_id": transaction.id}


@router.post("/circulation/extend")
async def extend_book_route(
    transaction_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Extend a book's due date (Librarian/Admin only)."""
    transaction = extend_book(db, transaction_id)
    return {
        "message": f"Book extended successfully (Extension {transaction.extension_count}/2)",
        "new_due_date": transaction.due_date.isoformat()
    }


@router.get("/transactions")
async def list_transactions(
    status_filter: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    book_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all transactions with book and user details."""
    from datetime import datetime, timedelta
    
    query = db.query(Transaction).join(Book).join(User)
    
    if status_filter:
        query = query.filter(Transaction.status == status_filter)
    
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    
    if book_id:
        query = query.filter(Transaction.book_id == book_id)
    
    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    # Build response with detailed information
    result = []
    for txn in transactions:
        # Check if overdue
        is_overdue = txn.status == "Overdue" or (txn.status == "Issued" and txn.due_date < datetime.utcnow())
        
        # Check if due soon (within 3 days)
        days_until_due = (txn.due_date - datetime.utcnow()).days if txn.status in ["Issued", "Overdue"] else None
        is_due_soon = days_until_due is not None and 0 <= days_until_due <= 3
        
        result.append({
            "id": txn.id,
            "book_id": txn.book_id,
            "user_id": txn.user_id,
            "book_acc_no": txn.book.acc_no,
            "book_title": txn.book.title,
            "book_author": txn.book.author,
            "user_name": txn.user.full_name,
            "user_username": txn.user.username,
            "issue_date": txn.issue_date.isoformat(),
            "due_date": txn.due_date.isoformat(),
            "return_date": txn.return_date.isoformat() if txn.return_date else None,
            "extension_count": txn.extension_count,
            "status": txn.status,
            "notes": txn.notes,
            "is_overdue": is_overdue,
            "is_due_soon": is_due_soon,
            "days_until_due": days_until_due
        })
    
    return result


# User Management Routes
@router.get("/user/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current logged-in user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active
    }


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all users (Admin only)."""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at
        }
        for u in users
    ]


@router.post("/users")
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new user (Admin only)."""
    from app.auth import get_password_hash
    
    # Check if username or email already exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Validate role
    if role not in ["admin", "viewer", "librarian"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin', 'viewer', or 'librarian'")
    
    # Create new user
    new_user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "is_active": new_user.is_active
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    email: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a user (Admin only)."""
    from app.auth import get_password_hash
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deactivating themselves
    if user_id == current_user.id and is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    # Update fields
    if email:
        # Check if email already exists for another user
        existing = db.query(User).filter(User.email == email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = email
    
    if full_name:
        user.full_name = full_name
    
    if role:
        if role not in ["admin", "viewer", "librarian"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin', 'viewer', or 'librarian'")
        user.role = role
    
    if is_active is not None:
        user.is_active = is_active
    
    if password:
        user.hashed_password = get_password_hash(password)
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a user (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Check if user has active transactions
    active_transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.status.in_(["Issued", "Overdue"])
    ).count()
    
    if active_transactions > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete user with {active_transactions} active transaction(s). Return all books first."
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/subjects")
async def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unique subjects for filtering."""
    subjects = db.query(Book.subject).filter(
        Book.subject != None,
        Book.subject != ""
    ).distinct().all()
    return [s[0] for s in subjects]


@router.post("/circulation/update-overdue")
async def update_overdue_status_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update overdue status for all transactions."""
    from app.circulation import update_overdue_status
    
    updated_count = update_overdue_status(db)
    
    return {
        "message": f"Updated {updated_count} transaction(s) to overdue status",
        "updated_count": updated_count
    }


@router.get("/transactions/active")
async def list_active_transactions(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Get all active transactions (Issued/Overdue) with book and user details (Librarian/Admin only)."""
    from datetime import datetime
    
    # Query transactions with joins
    query = db.query(Transaction).filter(
        Transaction.status.in_(["Issued", "Overdue"])
    ).join(Book).join(User)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Book.acc_no.ilike(search_pattern),
                Book.title.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
                User.username.ilike(search_pattern)
            )
        )
    
    transactions = query.offset(skip).limit(limit).all()
    
    # Build response with detailed information
    result = []
    for txn in transactions:
        # Check if overdue
        is_overdue = txn.due_date < datetime.utcnow() if txn.status == "Issued" else txn.status == "Overdue"
        
        result.append({
            "id": txn.id,
            "book_id": txn.book_id,
            "user_id": txn.user_id,
            "book_acc_no": txn.book.acc_no,
            "book_title": txn.book.title,
            "book_author": txn.book.author,
            "book_storage_loc": txn.book.storage_loc,
            "user_name": txn.user.full_name,
            "user_username": txn.user.username,
            "issue_date": txn.issue_date.isoformat(),
            "due_date": txn.due_date.isoformat(),
            "extension_count": txn.extension_count,
            "status": txn.status,
            "notes": txn.notes,
            "is_overdue": is_overdue
        })
    
    return result


@router.get("/transactions/extendable")
async def list_extendable_transactions(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_librarian_or_admin)
):
    """Get all active transactions (Issued/Overdue) with extendability status (Librarian/Admin only)."""
    from datetime import datetime, timedelta
    
    # Query all active transactions (not just extendable ones)
    query = db.query(Transaction).filter(
        Transaction.status.in_(["Issued", "Overdue"])
    ).join(Book).join(User)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Book.acc_no.ilike(search_pattern),
                Book.title.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
                User.username.ilike(search_pattern)
            )
        )
    
    transactions = query.offset(skip).limit(limit).all()
    
    # Build response with detailed information
    result = []
    for txn in transactions:
        # Check if overdue
        is_overdue = txn.due_date < datetime.utcnow() if txn.status == "Issued" else txn.status == "Overdue"
        
        # Check if can be extended
        can_extend = txn.extension_count < 2
        
        # Calculate new due date (current + 7 days)
        new_due_date = txn.due_date + timedelta(days=7)
        
        result.append({
            "id": txn.id,
            "book_id": txn.book_id,
            "user_id": txn.user_id,
            "book_acc_no": txn.book.acc_no,
            "book_title": txn.book.title,
            "book_author": txn.book.author,
            "book_storage_loc": txn.book.storage_loc,
            "user_name": txn.user.full_name,
            "user_username": txn.user.username,
            "issue_date": txn.issue_date.isoformat(),
            "due_date": txn.due_date.isoformat(),
            "new_due_date": new_due_date.isoformat(),
            "extension_count": txn.extension_count,
            "remaining_extensions": 2 - txn.extension_count,
            "can_extend": can_extend,
            "status": txn.status,
            "notes": txn.notes,
            "is_overdue": is_overdue
        })
    
    return result

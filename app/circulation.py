"""Circulation module for Issue, Retrieve, and Extend operations."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import Book, Transaction, User


def issue_book(db: Session, book_id: int, user_id: int, due_date: datetime, notes: str = None) -> Transaction:
    """
    Issue a book to a user.
    
    Validates:
    - Book exists and is not already issued
    - User exists
    
    Returns the created transaction.
    """
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Check if book is already issued
    if book.is_issued:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book '{book.title}' (Acc No: {book.acc_no}) is already issued"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Create transaction
    transaction = Transaction(
        book_id=book_id,
        user_id=user_id,
        issue_date=datetime.utcnow(),
        due_date=due_date,
        status="Issued",
        notes=notes
    )
    
    # Mark book as issued
    book.is_issued = True
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction


def retrieve_book(db: Session, transaction_id: int, notes: str = None) -> Transaction:
    """
    Retrieve (return) a book.
    
    Validates:
    - Transaction exists and is active (Issued or Overdue)
    
    Returns the updated transaction.
    """
    # Get transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    # Check if transaction is active
    if transaction.status == "Returned":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book has already been returned"
        )
    
    # Get book
    book = db.query(Book).filter(Book.id == transaction.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated book not found"
        )
    
    # Update transaction
    transaction.return_date = datetime.utcnow()
    transaction.status = "Returned"
    if notes:
        transaction.notes = f"{transaction.notes}\n{notes}" if transaction.notes else notes
    
    # Mark book as available
    book.is_issued = False
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


def extend_book(db: Session, transaction_id: int) -> Transaction:
    """
    Extend the due date of a book by 7 days.
    
    Validates:
    - Transaction exists and is active
    - Extension count is less than 2
    
    Returns the updated transaction.
    """
    # Get transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    # Check if transaction is active
    if transaction.status == "Returned":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot extend a returned book"
        )
    
    # Check extension limit
    if transaction.extension_count >= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum extension limit (2) reached for this book"
        )
    
    # Extend due date by 7 days
    transaction.due_date = transaction.due_date + timedelta(days=7)
    transaction.extension_count += 1
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


def update_overdue_status(db: Session):
    """
    Update the status of all issued transactions that are past their due date.
    This should be run periodically (e.g., daily).
    """
    now = datetime.utcnow()
    overdue_transactions = db.query(Transaction).filter(
        Transaction.status == "Issued",
        Transaction.due_date < now
    ).all()
    
    for transaction in overdue_transactions:
        transaction.status = "Overdue"
    
    if overdue_transactions:
        db.commit()
    
    return len(overdue_transactions)

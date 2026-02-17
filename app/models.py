"""SQLAlchemy models for TLC Nexus."""
from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User model for authentication and RBAC."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")  # admin, librarian, or viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")


class Book(Base):
    """Book model for physical inventory only."""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    acc_no = Column(String(50), unique=True, nullable=False, index=True)
    author = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    publisher_info = Column(Text)
    subject = Column(Text)
    class_no = Column(String(50))
    year = Column(Integer)
    isbn = Column(String(20))
    language = Column(String(50), nullable=True, default="English")
    storage_loc = Column(String(50), nullable=False)  # Format: TIC-R-\d+-S-\d+
    is_issued = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="book")
    digital_links = relationship("BookDigitalLink", back_populates="book")


class Transaction(Base):
    """Transaction model for circulation management."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    issue_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    extension_count = Column(Integer, default=0, nullable=False)
    status = Column(String(20), nullable=False, default="Issued")  # Issued, Returned, Overdue
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    book = relationship("Book", back_populates="transactions")
    user = relationship("User", back_populates="transactions")


class DigitalBook(Base):
    """Standalone digital book model - independent from physical inventory."""
    __tablename__ = "digital_books"

    # Primary Information
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False, index=True)
    author = Column(Text, nullable=False, index=True)
    
    # Digital-Specific Metadata
    file_path = Column(Text, nullable=False)  # Path in /library_vault/digital_books/
    file_size = Column(Integer)  # Size in bytes
    file_format = Column(String(10), nullable=False, default="pdf")  # pdf, epub, mobi
    
    # Additional Metadata
    publisher = Column(Text, nullable=True)
    publication_year = Column(Integer, nullable=True)
    isbn = Column(String(20), nullable=True, index=True)
    subject = Column(Text, nullable=True, index=True)
    description = Column(Text, nullable=True)
    language = Column(String(20), default="English")
    
    # Categories and Tags
    category = Column(String(100), nullable=True)  # Textbook, Reference, Fiction, etc.
    tags = Column(Text, nullable=True)  # Comma-separated tags
    
    # Statistics
    view_count = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploader = relationship("User")
    physical_links = relationship("BookDigitalLink", back_populates="digital_book")


class BookDigitalLink(Base):
    """Optional: Link physical books to digital resources (many-to-many)."""
    __tablename__ = "book_digital_links"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    digital_book_id = Column(Integer, ForeignKey("digital_books.id"), nullable=False)
    link_type = Column(String(20), default="same_edition")  # same_edition, different_edition, related
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    book = relationship("Book", back_populates="digital_links")
    digital_book = relationship("DigitalBook", back_populates="physical_links")


class PasswordResetToken(Base):
    """Password reset token model for secure password recovery."""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    token_type = Column(String(20), nullable=False, default="admin_generated")  # admin_generated, emergency
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    is_used = Column(Boolean, default=False, nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who generated
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="reset_tokens")
    admin = relationship("User", foreign_keys=[generated_by])


class PasswordHistory(Base):
    """Password history model to prevent password reuse."""
    __tablename__ = "password_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Self or admin
    change_reason = Column(String(50), nullable=True)  # "user_change", "admin_reset", "forgot_password"
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="password_history")
    changed_by_user = relationship("User", foreign_keys=[changed_by])


class Vendor(Base):
    """Vendor model for tracking magazine suppliers."""
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    contact_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    issues = relationship("MagazineIssue", back_populates="vendor")


class Magazine(Base):
    """Magazine master model for tracking titles and languages."""
    __tablename__ = "magazines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    language = Column(String(50), default="English")
    frequency = Column(String(50), nullable=True)  # Monthly, Weekly, etc.
    category = Column(String(100), nullable=True)  # Technical, General, etc.
    cover_image = Column(String(255), nullable=True)  # Path to cover image
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    issues = relationship("MagazineIssue", back_populates="magazine", cascade="all, delete-orphan")


class MagazineIssue(Base):
    """Magazine issue model for tracking received copies."""
    __tablename__ = "magazine_issues"

    id = Column(Integer, primary_key=True, index=True)
    magazine_id = Column(Integer, ForeignKey("magazines.id"), nullable=False)
    issue_description = Column(String(100), nullable=False)  # e.g., "January 2024" or "Vol 45, Issue 2"
    received_date = Column(DateTime, default=datetime.utcnow)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    magazine = relationship("Magazine", back_populates="issues")
    vendor = relationship("Vendor", back_populates="issues")

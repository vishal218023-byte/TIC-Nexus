"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
import re


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    full_name: str
    role: str = Field(default="viewer", pattern="^(admin|viewer)$")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Book Schemas (Physical Books Only)
class BookCreate(BaseModel):
    acc_no: str = Field(..., min_length=1, max_length=50)
    author: str
    title: str
    publisher_info: Optional[str] = None
    subject: Optional[str] = None
    class_no: Optional[str] = None
    year: Optional[int] = Field(None, ge=1800, le=2100)
    isbn: Optional[str] = None
    language: Optional[str] = "English"
    storage_loc: str

    @validator('storage_loc')
    def validate_storage_location(cls, v):
        """Validate storage location format: TIC-R-\d+-S-\d+"""
        pattern = r'^TIC-R-\d+-S-\d+$'
        if not re.match(pattern, v):
            raise ValueError(
                'Storage location must match format: TIC-R-[RackNumber]-S-[ShelfNumber] '
                '(e.g., TIC-R-1-S-3)'
            )
        return v


class BookUpdate(BaseModel):
    author: Optional[str] = None
    title: Optional[str] = None
    publisher_info: Optional[str] = None
    subject: Optional[str] = None
    class_no: Optional[str] = None
    year: Optional[int] = Field(None, ge=1800, le=2100)
    isbn: Optional[str] = None
    language: Optional[str] = None
    storage_loc: Optional[str] = None

    @validator('storage_loc')
    def validate_storage_location(cls, v):
        if v is not None:
            pattern = r'^TIC-R-\d+-S-\d+$'
            if not re.match(pattern, v):
                raise ValueError(
                    'Storage location must match format: TIC-R-[RackNumber]-S-[ShelfNumber]'
                )
        return v


class BookResponse(BaseModel):
    id: int
    acc_no: str
    author: str
    title: str
    publisher_info: Optional[str]
    subject: Optional[str]
    class_no: Optional[str]
    year: Optional[int]
    isbn: Optional[str]
    language: Optional[str]
    storage_loc: str
    is_issued: bool
    created_at: datetime
    updated_at: datetime
    digital_book_id: Optional[int] = None

    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionIssue(BaseModel):
    book_id: int
    user_id: int
    due_date: datetime
    notes: Optional[str] = None


class TransactionExtend(BaseModel):
    transaction_id: int


class TransactionReturn(BaseModel):
    transaction_id: int
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    book_id: int
    user_id: int
    issue_date: datetime
    due_date: datetime
    return_date: Optional[datetime]
    extension_count: int
    status: str
    notes: Optional[str]

    class Config:
        from_attributes = True


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_books: int
    total_issued: int
    total_overdue: int
    total_users: int
    digital_library_count: int


class SubjectDistribution(BaseModel):
    subject: str
    count: int


# Digital Library Schemas
class DigitalBookCreate(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    publisher: Optional[str] = None
    publication_year: Optional[int] = Field(None, ge=1800, le=2100)
    isbn: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    language: str = Field(default="English")
    category: Optional[str] = None
    tags: Optional[str] = None  # Comma-separated tags

    @validator('tags')
    def validate_tags(cls, v):
        """Ensure tags are properly formatted."""
        if v and v.strip():
            # Clean up tags: remove extra spaces, ensure comma separation
            tags_list = [tag.strip() for tag in v.split(',') if tag.strip()]
            return ', '.join(tags_list)
        return v


class DigitalBookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = Field(None, ge=1800, le=2100)
    isbn: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None

    @validator('tags')
    def validate_tags(cls, v):
        if v and v.strip():
            tags_list = [tag.strip() for tag in v.split(',') if tag.strip()]
            return ', '.join(tags_list)
        return v


class DigitalBookResponse(BaseModel):
    id: int
    title: str
    author: str
    file_path: str
    file_size: Optional[int]
    file_format: str
    publisher: Optional[str]
    publication_year: Optional[int]
    isbn: Optional[str]
    subject: Optional[str]
    description: Optional[str]
    language: str
    category: Optional[str]
    tags: Optional[str]
    view_count: int
    download_count: int
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DigitalBookDetailResponse(DigitalBookResponse):
    """Extended response with uploader information and linked physical books."""
    uploader_name: Optional[str] = None
    linked_physical_books: list = []

    class Config:
        from_attributes = True


# Book-Digital Link Schemas
class BookDigitalLinkCreate(BaseModel):
    book_id: int
    digital_book_id: int
    link_type: str = Field(default="same_edition", pattern="^(same_edition|different_edition|related)$")
    notes: Optional[str] = None


class BookDigitalLinkResponse(BaseModel):
    id: int
    book_id: int
    digital_book_id: int
    link_type: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Password Reset Schemas
class PasswordResetTokenGenerate(BaseModel):
    user_id: int


class PasswordResetTokenResponse(BaseModel):
    id: int
    user_id: int
    token: str
    expires_at: datetime
    is_used: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PasswordResetWithToken(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordStrengthResponse(BaseModel):
    strength: str  # weak, medium, strong
    score: int  # 0-100
    feedback: list[str]

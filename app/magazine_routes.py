"""FastAPI router for magazine management."""
import os
import shutil
import uuid
from datetime import datetime, date
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Magazine, MagazineIssue, Vendor, User
from app.schemas import (
    MagazineCreate, MagazineUpdate, MagazineResponse, 
    MagazineIssueCreate, MagazineIssueResponse,
    VendorCreate, VendorResponse, MagazineDetailResponse
)
from app.auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api", tags=["magazines"])

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAGAZINE_UPLOADS = os.path.join(BASE_DIR, "static", "uploads", "magazines")
os.makedirs(MAGAZINE_UPLOADS, exist_ok=True)


# Vendor Routes
@router.post("/vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new vendor."""
    db_vendor = db.query(Vendor).filter(Vendor.name == vendor.name).first()
    if db_vendor:
        raise HTTPException(status_code=400, detail="Vendor with this name already exists")
    
    new_vendor = Vendor(
        name=vendor.name,
        contact_details=vendor.contact_details
    )
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor


@router.get("/vendors", response_model=List[VendorResponse])
async def get_vendors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all vendors."""
    return db.query(Vendor).order_by(Vendor.name).all()


# Magazine Routes
@router.post("/magazines", response_model=MagazineResponse, status_code=status.HTTP_201_CREATED)
async def create_magazine(
    title: str = Form(...),
    language: str = Form("English"),
    frequency: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    cover_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new magazine master record."""
    if current_user.role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_magazine = Magazine(
        title=title,
        language=language,
        frequency=frequency,
        category=category
    )
    
    if cover_image:
        # Save cover image
        file_ext = os.path.splitext(cover_image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(MAGAZINE_UPLOADS, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(cover_image.file, buffer)
        
        new_magazine.cover_image = f"/static/uploads/magazines/{unique_filename}"
    
    db.add(new_magazine)
    db.commit()
    db.refresh(new_magazine)
    return new_magazine


@router.get("/magazines", response_model=List[MagazineResponse])
async def get_magazines(
    q: Optional[str] = None,
    language: Optional[str] = Query(None),
    frequency: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all magazines with optional filtering."""
    query = db.query(Magazine)
    
    if q:
        query = query.filter(
            or_(
                Magazine.title.ilike(f"%{q}%"),
                Magazine.language.ilike(f"%{q}%"),
                Magazine.category.ilike(f"%{q}%")
            )
        )
    
    if language:
        query = query.filter(Magazine.language == language)
    
    if frequency:
        query = query.filter(Magazine.frequency == frequency)
    
    if category:
        query = query.filter(Magazine.category == category)
        
    return query.order_by(Magazine.title).all()


@router.get("/magazines/filters/languages")
async def get_magazine_languages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unique magazine languages for filtering."""
    languages = db.query(Magazine.language).filter(
        Magazine.language != None,
        Magazine.language != ""
    ).distinct().all()
    return [l[0] for l in languages]


@router.get("/magazines/filters/frequencies")
async def get_magazine_frequencies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unique magazine frequencies for filtering."""
    frequencies = db.query(Magazine.frequency).filter(
        Magazine.frequency != None,
        Magazine.frequency != ""
    ).distinct().all()
    return [f[0] for f in frequencies]


@router.get("/magazines/filters/categories")
async def get_magazine_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unique magazine categories for filtering."""
    categories = db.query(Magazine.category).filter(
        Magazine.category != None,
        Magazine.category != ""
    ).distinct().all()
    return [c[0] for c in categories]


@router.put("/magazines/{magazine_id}", response_model=MagazineResponse)
async def update_magazine(
    magazine_id: int,
    magazine_update: MagazineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update magazine details."""
    if current_user.role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_magazine = db.query(Magazine).filter(Magazine.id == magazine_id).first()
    if not db_magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")
    
    update_data = magazine_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_magazine, key, value)
    
    db.commit()
    db.refresh(db_magazine)
    return db_magazine


@router.post("/magazines/{magazine_id}/upload-cover", response_model=MagazineResponse)
async def upload_magazine_cover(
    magazine_id: int,
    cover_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload or replace magazine cover image."""
    if current_user.role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_magazine = db.query(Magazine).filter(Magazine.id == magazine_id).first()
    if not db_magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")
    
    # Save cover image
    file_ext = os.path.splitext(cover_image.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(MAGAZINE_UPLOADS, unique_filename)
    
    # Remove old image if exists
    if db_magazine.cover_image:
        old_path = os.path.join(BASE_DIR, db_magazine.cover_image.lstrip("/"))
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(cover_image.file, buffer)
    
    db_magazine.cover_image = f"/static/uploads/magazines/{unique_filename}"
    db.commit()
    db.refresh(db_magazine)
    return db_magazine


# Issue Routes
@router.post("/magazines/issues", response_model=MagazineIssueResponse, status_code=status.HTTP_201_CREATED)
async def log_magazine_issue(
    issue: MagazineIssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log a new received magazine issue."""
    if current_user.role not in ["admin", "librarian"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Robustly handle received_date
    rd = None
    if issue.received_date:
        if isinstance(issue.received_date, datetime):
            rd = issue.received_date
        elif isinstance(issue.received_date, date):
            # Convert date to datetime at midnight
            rd = datetime.combine(issue.received_date, datetime.min.time())
        elif isinstance(issue.received_date, str):
            try:
                # Try full ISO format first
                rd = datetime.fromisoformat(issue.received_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try YYYY-MM-DD format
                    rd = datetime.strptime(issue.received_date, "%Y-%m-%d")
                except ValueError:
                    rd = datetime.utcnow()
        else:
            rd = datetime.utcnow()
    else:
        rd = datetime.utcnow()
    
    new_issue = MagazineIssue(
        magazine_id=issue.magazine_id,
        issue_description=issue.issue_description,
        received_date=rd,
        vendor_id=issue.vendor_id,
        remarks=issue.remarks
    )
    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)
    return new_issue


@router.get("/magazines/{magazine_id}/issues", response_model=List[MagazineIssueResponse])
async def get_magazine_issues(
    magazine_id: int,
    db: Session = Depends(get_db)
):
    """List issues for a specific magazine."""
    issues = db.query(MagazineIssue).filter(MagazineIssue.magazine_id == magazine_id)\
               .order_by(MagazineIssue.received_date.desc()).all()
    
    # Add vendor names
    results = []
    for issue in issues:
        vendor = db.query(Vendor).filter(Vendor.id == issue.vendor_id).first()
        issue_resp = MagazineIssueResponse.from_orm(issue)
        issue_resp.vendor_name = vendor.name if vendor else "Unknown"
        results.append(issue_resp)
    
    return results


# Public Routes
@router.get("/public/magazines", response_model=List[MagazineDetailResponse])
async def get_public_magazines(
    db: Session = Depends(get_db)
):
    """Publicly list active magazines with their latest issues."""
    magazines = db.query(Magazine).filter(Magazine.is_active == True).order_by(Magazine.title).all()
    
    results = []
    for mag in magazines:
        # Get latest 5 issues
        issues = db.query(MagazineIssue).filter(MagazineIssue.magazine_id == mag.id)\
                   .order_by(MagazineIssue.received_date.desc()).limit(5).all()
        
        # Prepare issue responses
        issue_list = []
        for issue in issues:
            vendor = db.query(Vendor).filter(Vendor.id == issue.vendor_id).first()
            i_resp = MagazineIssueResponse.from_orm(issue)
            i_resp.vendor_name = vendor.name if vendor else "Unknown"
            issue_list.append(i_resp)
            
        mag_resp = MagazineDetailResponse.from_orm(mag)
        mag_resp.recent_issues = issue_list
        results.append(mag_resp)
        
    return results

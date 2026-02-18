import pandas as pd
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for database imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Magazine, Vendor, MagazineIssue

def migrate_magazines():
    path = 'migrations/Magzines.xlsx'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        # Based on inspection, the first row is data, no header
        df = pd.read_excel(path, header=None)
        print(f"Read {len(df)} magazine rows.")
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return

    db = SessionLocal()
    try:
        # 1. Get or Create Default Vendor
        vendor_name = "Initial Import"
        vendor = db.query(Vendor).filter(Vendor.name == vendor_name).first()
        if not vendor:
            vendor = Vendor(name=vendor_name, contact_details="Imported from legacy records")
            db.add(vendor)
            db.commit()
            db.refresh(vendor)
            print(f"✓ Vendor created: {vendor_name}")
        
        mag_count = 0
        issue_count = 0
        
        for idx, row in df.iterrows():
            title = str(row[0]).strip() if pd.notna(row[0]) else None
            language = str(row[1]).strip() if pd.notna(row[1]) else "English"
            
            if not title:
                continue
            
            # 2. Check if magazine exists
            magazine = db.query(Magazine).filter(Magazine.title == title).first()
            if not magazine:
                magazine = Magazine(
                    title=title,
                    language=language,
                    category="General",
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(magazine)
                db.flush()
                mag_count += 1
            
            # 3. Check if issue exists
            existing_issue = db.query(MagazineIssue).filter(
                MagazineIssue.magazine_id == magazine.id,
                MagazineIssue.issue_description == "Legacy Record"
            ).first()
            
            if not existing_issue:
                issue = MagazineIssue(
                    magazine_id=magazine.id,
                    issue_description="Legacy Record",
                    received_date=datetime.utcnow(),
                    vendor_id=vendor.id,
                    remarks="Imported during system migration"
                )
                db.add(issue)
                issue_count += 1

        db.commit()
        print("\n✓ Magazine Migration Complete!")
        print(f"  - New Magazines Added: {mag_count}")
        print(f"  - Legacy Issues Logged: {issue_count}")
        print(f"  - Vendor used: {vendor_name}")

    except Exception as e:
        db.rollback()
        print(f"✗ Error during magazine migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_magazines()

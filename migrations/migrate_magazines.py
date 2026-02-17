"""Migration script for Magazines.

Migrates data from 'Magzines.xlsx' to the TIC Nexus database.
This script populates the 'magazines', 'vendors', and 'magazine_issues' tables.
"""
import sys
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine, Base
from app.models import Magazine, Vendor, MagazineIssue

class MagazineMigrator:
    def __init__(self, excel_path: str, dry_run: bool = True):
        self.excel_path = excel_path
        self.dry_run = dry_run
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.stats = {'added_magazines': 0, 'added_issues': 0, 'errors': 0}
        self.default_vendor = None

    def get_or_create_vendor(self, name="Initial Import"):
        vendor = self.db.query(Vendor).filter(Vendor.name == name).first()
        if not vendor:
            print(f"Creating default vendor: {name}")
            vendor = Vendor(name=name, contact_details="Imported from legacy records")
            if not self.dry_run:
                self.db.add(vendor)
                self.db.commit()
                self.db.refresh(vendor)
        return vendor

    def run(self):
        status_text = 'DRY RUN' if self.dry_run else 'EXECUTING'
        print(f"\n{status_text} MAGAZINE MIGRATION...")
        print("-" * 75)

        # Load Excel (No header)
        try:
            # Based on inspection, the first row is data, so header=None
            df = pd.read_excel(self.excel_path, header=None)
        except Exception as e:
            print(f"Error reading Excel: {e}")
            return

        self.default_vendor = self.get_or_create_vendor()

        for idx, row in df.iterrows():
            title = str(row[0]).strip() if pd.notna(row[0]) else None
            language = str(row[1]).strip() if pd.notna(row[1]) else "English"
            
            if not title:
                continue
            
            # Check if magazine exists
            existing = self.db.query(Magazine).filter(Magazine.title == title).first()
            if existing:
                mag_id = existing.id
            else:
                new_mag = Magazine(
                    title=title,
                    language=language,
                    category="General",
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                if not self.dry_run:
                    self.db.add(new_mag)
                    self.db.flush()
                    mag_id = new_mag.id
                else:
                    mag_id = idx # Mock ID
                self.stats['added_magazines'] += 1
                if self.stats['added_magazines'] < 10:
                    print(f"Registering Magazine: {title} ({language})")
                elif self.stats['added_magazines'] == 10:
                    print("...")

            # For the migration, we'll create one "Initial Legacy Issue" for each
            new_issue = MagazineIssue(
                magazine_id=mag_id,
                issue_description="Legacy Record",
                received_date=datetime.utcnow(),
                vendor_id=self.default_vendor.id if self.default_vendor else 1,
                remarks="Imported during system migration"
            )
            
            if not self.dry_run:
                self.db.add(new_issue)
                self.stats['added_issues'] += 1
            else:
                self.stats['added_issues'] += 1

        if not self.dry_run:
            self.db.commit()
            print("\n✓ Magazine Migration Committed Successfully!")
        
        print("-" * 75)
        print(f"Summary: {self.stats['added_magazines']} Magazines Registered, {self.stats['added_issues']} Issues Logged")
        self.db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', help='Actually write to database')
    args = parser.parse_args()
    
    # Path relative to project root
    excel_file = 'migrations/Magzines.xlsx'
    if not Path(excel_file).exists():
        print(f"File not found: {excel_file}")
        sys.exit(1)
        
    migrator = MagazineMigrator(excel_file, dry_run=not args.execute)
    migrator.run()

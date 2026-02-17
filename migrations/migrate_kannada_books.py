"""Specialized migration script for Kannada Books.

Migrates data from 'Kannada Books.xlsx' to the TIC Nexus database.
Rules:
- Subject: 'General'
- Language: 'Kannada'
- Storage Location: 'TIC-C-X-S-Y' (C for Cupboard)
"""
import sys
import argparse
import pandas as pd
import re
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import SessionLocal
from app.models import Book

class KannadaMigrator:
    def __init__(self, excel_path: str, dry_run: bool = True):
        self.excel_path = excel_path
        self.dry_run = dry_run
        self.db = SessionLocal()
        self.stats = {'added': 0, 'skipped': 0, 'errors': 0}

    def clean_location(self, loc_str):
        """Convert 'C-1,S1' to 'TIC-C-1-S-1'"""
        if pd.isna(loc_str) or str(loc_str).strip() == '':
            return "TIC-C-1-S-1"
        
        # Match C-1,S1 or C-1 S1
        match = re.search(r'C[-\s]*(\d+)[,\s]*S(\d+)', str(loc_str), re.IGNORECASE)
        if match:
            cupboard = match.group(1)
            shelf = match.group(2)
            return f"TIC-C-{cupboard}-S-{shelf}"
        return "TIC-C-1-S-1"

    def run(self):
        print(f"\n{'DRY RUN' if self.dry_run else 'EXECUTING'} MIGRATION...")
        print("-" * 60)

        # Load Excel (No header)
        try:
            df = pd.read_excel(self.excel_path, header=None)
        except Exception as e:
            print(f"Error reading Excel: {e}")
            return

        for idx, row in df.iterrows():
            if pd.isna(row[1]): continue  # Skip empty rows
            
            acc_no = str(row[1]).strip().upper()
            author = str(row[2]).strip() if pd.notna(row[2]) else "Unknown Author"
            title = str(row[3]).strip() if pd.notna(row[3]) else "Untitled"
            raw_loc = row[4]
            
            # Check if exists
            existing = self.db.query(Book).filter(Book.acc_no == acc_no).first()
            if existing:
                print(f"Skipping Duplicate: [{acc_no}] {title[:30]}...")
                self.stats['skipped'] += 1
                continue

            # Prepare Book Object
            target_loc = self.clean_location(raw_loc)
            
            new_book = Book(
                acc_no=acc_no,
                author=author,
                title=title,
                subject="General",
                language="Kannada",
                storage_loc=target_loc,
                is_issued=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            print(f"Adding: [{acc_no}] {title[:30]:<35} at {target_loc}")
            
            if not self.dry_run:
                try:
                    self.db.add(new_book)
                    self.db.flush()
                    self.stats['added'] += 1
                except Exception as e:
                    print(f"Error adding {acc_no}: {e}")
                    self.db.rollback()
                    self.stats['errors'] += 1
            else:
                self.stats['added'] += 1

        if not self.dry_run and self.stats['added'] > 0:
            self.db.commit()
            print("\n✓ Migration Committed Successfully!")
        
        print("-" * 60)
        print(f"Summary: {self.stats['added']} Added, {self.stats['skipped']} Skipped, {self.stats['errors']} Errors")
        self.db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', help='Actually write to database')
    args = parser.parse_args()
    
    migrator = KannadaMigrator('migrations/Kannada Books.xlsx', dry_run=not args.execute)
    migrator.run()

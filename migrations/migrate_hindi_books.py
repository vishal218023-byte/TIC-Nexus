"""Specialized migration script for Hindi Books.

Migrates data from 'Hindi Books.xlsx' to the TIC Nexus database.
Rules:
- Subject: Extracted from 'Subject ' column
- Language: 'Hindi'
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

from app.database import SessionLocal
from app.models import Book

class HindiMigrator:
    def __init__(self, excel_path: str, dry_run: bool = True):
        self.excel_path = excel_path
        self.dry_run = dry_run
        self.db = SessionLocal()
        self.stats = {'added': 0, 'skipped': 0, 'errors': 0}

    def clean_location(self, loc_str):
        """Convert 'C-1,S2' to 'TIC-C-1-S-2'"""
        if pd.isna(loc_str) or str(loc_str).strip() == '':
            return "TIC-C-1-S-2"
        
        # Match C-1,S2 or C-1 S2 or C1 S2
        match = re.search(r'C[-\s]*(\d+)[,\s]*S(\d+)', str(loc_str), re.IGNORECASE)
        if match:
            cupboard = match.group(1)
            shelf = match.group(2)
            return f"TIC-C-{cupboard}-S-{shelf}"
        return "TIC-C-1-S-2"

    def run(self):
        print(f"\n{'DRY RUN' if self.dry_run else 'EXECUTING'} HINDI MIGRATION...")
        print("-" * 75)

        # Load Excel (Has header)
        try:
            df = pd.read_excel(self.excel_path)
        except Exception as e:
            print(f"Error reading Excel: {e}")
            return

        for idx, row in df.iterrows():
            if pd.isna(row['Acc .No ']): continue
            
            acc_no = str(row['Acc .No ']).strip().upper()
            author = str(row['Author']).strip() if pd.notna(row['Author']) else "Unknown Author"
            title = str(row['Title']).strip() if pd.notna(row['Title']) else "Untitled"
            subject = str(row['Subject ']).strip() if pd.notna(row['Subject ']) else "General"
            raw_loc = row['Storage Location']
            
            # Check if exists
            existing = self.db.query(Book).filter(Book.acc_no == acc_no).first()
            if existing:
                if self.stats['skipped'] < 5:
                    print(f"Skipping Duplicate: [{acc_no}] {title[:30]}...")
                elif self.stats['skipped'] == 5:
                    print("...")
                self.stats['skipped'] += 1
                continue

            # Prepare Book Object
            target_loc = self.clean_location(raw_loc)
            
            new_book = Book(
                acc_no=acc_no,
                author=author,
                title=title,
                subject=subject,
                language="Hindi",
                storage_loc=target_loc,
                is_issued=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Print first few for verification
            if self.stats['added'] < 10:
                print(f"Adding: [{acc_no}] {title[:30]:<35} | Sub: {subject:<15} | Loc: {target_loc}")
            elif self.stats['added'] == 10:
                print("Processing remaining records...")

            if not self.dry_run:
                try:
                    self.db.add(new_book)
                    if (self.stats['added'] + 1) % 50 == 0:
                        self.db.flush()
                        print(f"  Processed {self.stats['added'] + 1} records...")
                    self.stats['added'] += 1
                except Exception as e:
                    print(f"\nError adding {acc_no}: {e}")
                    self.db.rollback()
                    self.stats['errors'] += 1
            else:
                self.stats['added'] += 1

        if not self.dry_run and self.stats['added'] > 0:
            self.db.commit()
            print("\n✓ Hindi Migration Committed Successfully!")
        
        print("-" * 75)
        print(f"Summary: {self.stats['added']} Added, {self.stats['skipped']} Skipped, {self.stats['errors']} Errors")
        self.db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', help='Actually write to database')
    args = parser.parse_args()
    
    migrator = HindiMigrator('migrations/Hindi Books.xlsx', dry_run=not args.execute)
    migrator.run()

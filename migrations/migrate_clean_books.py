import pandas as pd
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Add parent directory to path for database imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine
from app.models import Book, Base
from app.utils import format_subject

def clean_location(loc_str, default_prefix="R"):
    """Standardizes locations to TIC-R-X-S-Y or TIC-C-X-S-Y format."""
    if pd.isna(loc_str) or str(loc_str).strip() == '':
        return f"TIC-{default_prefix}-1-S-1"
    
    loc_str = str(loc_str).strip().upper()
    
    # Already in TIC format?
    if loc_str.startswith('TIC-'):
        return loc_str
    
    # Match R1-S1, C1-S1, etc.
    match = re.search(r'([RC])?[-\s]*(\d+)[,\s-]*S(\d+)', loc_str)
    if match:
        prefix = match.group(1) if match.group(1) else default_prefix
        rack = match.group(2)
        shelf = match.group(3)
        return f"TIC-{prefix}-{rack}-S-{shelf}"
    
    return f"TIC-{default_prefix}-1-S-1"

def migrate_clean_books():
    files = [
        ('English', 'migrations/English Books.xlsx', {
            'acc_no': 'ACC. NO', 'title': 'TITLE', 'author': 'AUTHOR', 
            'publisher': 'PUBLISHER / PLACE OF PUB', 'year': ' YEAR', 
            'isbn': 'ISBN', 'loc': 'RACK NO / SHELF NO', 'subject': 'SUBJECT', 'class': 'CLASS. NO'
        }),
        ('Hindi', 'migrations/Hindi Books.xlsx', {
            'acc_no': 'Acc .No ', 'title': 'Title', 'author': 'Author', 
            'publisher': None, 'year': None, 'isbn': None, 
            'loc': 'Storage Location', 'subject': 'Subject ', 'class': None
        }),
        ('Kannada', 'migrations/Kannada Books.xlsx', {
            'acc_no': 'Acc .No ', 'title': 'Title', 'author': 'Author', 
            'publisher': None, 'year': None, 'isbn': None, 
            'loc': 'Storage Location', 'subject': 'Subject ', 'class': None
        })
    ]

    all_rows = []
    print("Reading and standardizing data...")

    for lang, path, cols in files:
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_excel(path)
            df = df.dropna(how='all')
            
            for idx, row in df.iterrows():
                raw_acc = row.get(cols['acc_no'])
                if pd.isna(raw_acc) or str(raw_acc).strip() == '':
                    continue 
                
                acc_no = str(raw_acc).strip().upper()
                
                book_data = {
                    'acc_no': acc_no,
                    'title': str(row.get(cols['title'], 'Untitled')).strip(),
                    'author': str(row.get(cols['author'], 'Unknown Author')).strip(),
                    'publisher_info': str(row.get(cols['publisher'], '')) if cols['publisher'] and pd.notna(row.get(cols['publisher'])) else None,
                    'subject': format_subject(str(row.get(cols['subject'], 'General')).strip()),
                    'class_no': str(row.get(cols['class'], '')) if cols['class'] and pd.notna(row.get(cols['class'])) else None,
                    'language': lang,
                    'storage_loc': clean_location(row.get(cols['loc']), "R" if lang == 'English' else "C")
                }
                
                if cols['year'] and pd.notna(row.get(cols['year'])):
                    year_match = re.search(r'\d{4}', str(row[cols['year']]))
                    book_data['year'] = int(year_match.group()) if year_match else None
                else:
                    book_data['year'] = None
                    
                if cols['isbn'] and pd.notna(row.get(cols['isbn'])):
                    book_data['isbn'] = str(row[cols['isbn']]).replace('-', '').replace(' ', '').strip()
                else:
                    book_data['isbn'] = None
                    
                all_rows.append(book_data)
        except Exception as e:
            print(f"Error reading {path}: {e}")

    if not all_rows:
        print("No records found to migrate.")
        return

    master_df = pd.DataFrame(all_rows)
    acc_counts = master_df['acc_no'].value_counts()
    conflicted_ids = acc_counts[acc_counts > 1].index.tolist()
    clean_books_df = master_df[~master_df['acc_no'].isin(conflicted_ids)]
    
    print("\nMigration Analysis:")
    print(f"  Total records with IDs: {len(master_df)}")
    print(f"  Conflicted IDs skipped: {len(conflicted_ids)} (affecting {len(master_df) - len(clean_books_df)} rows)")
    print(f"  Clean records to migrate: {len(clean_books_df)}")
    
    db = SessionLocal()
    try:
        print("\nStarting migration...")
        batch_size = 100
        count = 0
        
        for _, row in clean_books_df.iterrows():
            book = Book(
                acc_no=row['acc_no'],
                author=row['author'],
                title=row['title'],
                publisher_info=row['publisher_info'],
                subject=row['subject'],
                class_no=row['class_no'],
                year=row['year'],
                isbn=row['isbn'],
                language=row['language'],
                storage_loc=row['storage_loc'],
                is_issued=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(book)
            count += 1
            
            if count % batch_size == 0:
                db.commit()
                print(f"  Migrated {count} records...")
        
        db.commit()
        print(f"\n✓ Migration complete! {count} clean books added to the database.")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_clean_books()

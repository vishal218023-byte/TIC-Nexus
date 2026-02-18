import pandas as pd
import os
import sys
from pathlib import Path

# Add parent directory to path for database imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Book

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass # Handle closing manually

files = [
    ('English', 'migrations/English Books.xlsx', {
        'acc_no': 'ACC. NO',
        'title': 'TITLE',
        'author': 'AUTHOR'
    }),
    ('Hindi', 'migrations/Hindi Books.xlsx', {
        'acc_no': 'Acc .No ',
        'title': 'Title',
        'author': 'Author'
    }),
    ('Kannada', 'migrations/Kannada Books.xlsx', {
        'acc_no': 'Acc .No ',
        'title': 'Title',
        'author': 'Author'
    })
]

all_acc_nos = {} # acc_no -> list of (source, title)

print("Analyzing Excel files for conflicts...")

for lang, path, cols in files:
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
    
    try:
        # Load all rows
        df = pd.read_excel(path)
        acc_col = cols['acc_no']
        title_col = cols['title']
        
        for idx, row in df.iterrows():
            raw_acc = row[acc_col]
            if pd.isna(raw_acc):
                continue
            
            acc_no = str(raw_acc).strip().upper()
            title = str(row[title_col]).strip() if pd.notna(row[title_col]) else "Untitled"
            
            if acc_no in all_acc_nos:
                all_acc_nos[acc_no].append((lang, title))
            else:
                all_acc_nos[acc_no] = [(lang, title)]
                
    except Exception as e:
        print(f"Error processing {path}: {e}")

# Identify duplicates across all files
print("\n--- Accession Number Conflict Report ---")
conflict_count = 0
for acc_no, entries in all_acc_nos.items():
    if len(entries) > 1:
        conflict_count += 1
        print(f"\nConflict for Acc No: {acc_no}")
        for lang, title in entries:
            print(f"  - [{lang}] {title}")

if conflict_count == 0:
    print("No conflicts found across the Excel files!")
else:
    print(f"\nTotal conflicts found: {conflict_count}")

# Check against database
db = SessionLocal()
try:
    db_books = db.query(Book.acc_no, Book.title).all()
    if db_books:
        print("\n--- Database Collisions ---")
        for db_acc, db_title in db_books:
            if db_acc.upper() in all_acc_nos:
                print(f"Collision with DB: {db_acc} | DB Title: {db_title} | Excel Title: {all_acc_nos[db_acc.upper()][0][1]}")
    else:
        print("\nDatabase is currently empty (verified).")
finally:
    db.close()

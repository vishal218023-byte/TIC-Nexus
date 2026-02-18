
import sqlite3
import os

db_path = os.path.join("data", "tic_nexus.db")

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current occurrences
    cursor.execute("SELECT count(*) FROM books WHERE storage_loc LIKE 'TLC-%'")
    count = cursor.fetchone()[0]
    print(f"Found {count} books with 'TLC-' prefix in storage_loc.")
    
    if count > 0:
        # Update TLC to TIC
        cursor.execute("UPDATE books SET storage_loc = REPLACE(storage_loc, 'TLC-', 'TIC-') WHERE storage_loc LIKE 'TLC-%'")
        conn.commit()
        print(f"Successfully updated {cursor.rowcount} records to 'TIC-' prefix.")
    else:
        print("No records found with 'TLC-' prefix.")
        
    conn.close()
except Exception as e:
    print(f"An error occurred: {e}")
    if conn:
        conn.rollback()
        conn.close()

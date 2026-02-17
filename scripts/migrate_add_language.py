import sqlite3
import os

db_path = os.path.join('data', 'tic_nexus.db')

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(books)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'language' in columns:
        print("Column 'language' already exists in 'books' table.")
    else:
        cursor.execute("ALTER TABLE books ADD COLUMN language VARCHAR(50) DEFAULT 'English'")
        conn.commit()
        print("Migration successful: 'language' column added to 'books' table.")
        
    conn.close()
except Exception as e:
    print(f"An error occurred: {e}")
    exit(1)

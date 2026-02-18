import pandas as pd
import os

files = [
    'migrations/English Books.xlsx',
    'migrations/Hindi Books.xlsx',
    'migrations/Kannada Books.xlsx'
]

for f in files:
    if not os.path.exists(f):
        print(f"File not found: {f}")
        continue
    try:
        df = pd.read_excel(f, nrows=5)
        print(f"\n--- {f} ---")
        print(f"Columns: {df.columns.tolist()}")
        print("First 3 rows:")
        print(df.to_string())
    except Exception as e:
        print(f"Error reading {f}: {e}")

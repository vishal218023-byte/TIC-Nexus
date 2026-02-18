import pandas as pd
import os

path = 'migrations/Magzines.xlsx'
if not os.path.exists(path):
    print(f"File not found: {path}")
else:
    try:
        df = pd.read_excel(path, nrows=5)
        print(f"Columns: {df.columns.tolist()}")
        print("First 3 rows:")
        print(df.to_string())
    except Exception as e:
        print(f"Error reading {path}: {e}")

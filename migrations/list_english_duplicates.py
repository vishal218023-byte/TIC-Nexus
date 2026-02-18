import pandas as pd
import os

path = 'migrations/English Books.xlsx'
if not os.path.exists(path):
    print(f"File not found: {path}")
else:
    df = pd.read_excel(path)
    df_clean = df[df['ACC. NO'].notna()].copy()
    df_clean['ACC. NO'] = df_clean['ACC. NO'].astype(str).str.strip().str.upper()
    
    duplicates = df_clean[df_clean.duplicated(subset=['ACC. NO'], keep=False)]
    
    if duplicates.empty:
        print("No internal duplicates found in English Books.xlsx")
    else:
        grouped = duplicates.groupby('ACC. NO')
        print(f"--- Internal Duplicates in English Books.xlsx ({len(grouped)} unique IDs) ---")
        for acc_no, group in grouped:
            print(f"\nAcc No: {acc_no}")
            for idx, row in group.iterrows():
                title = str(row['TITLE']).strip() if pd.notna(row['TITLE']) else "Untitled"
                print(f"  - {title}")

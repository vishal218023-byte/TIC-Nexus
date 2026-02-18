import pandas as pd
import os

def create_formatted_conflict_report():
    files = [
        ('English', 'migrations/English Books.xlsx', {
            'acc_no': 'ACC. NO',
            'title': 'TITLE',
            'author': 'AUTHOR',
            'subject': 'SUBJECT'
        }),
        ('Hindi', 'migrations/Hindi Books.xlsx', {
            'acc_no': 'Acc .No ',
            'title': 'Title',
            'author': 'Author',
            'subject': 'Subject '
        }),
        ('Kannada', 'migrations/Kannada Books.xlsx', {
            'acc_no': 'Acc .No ',
            'title': 'Title',
            'author': 'Author',
            'subject': 'Subject '
        })
    ]

    all_data = []
    
    print("Reading source files...")
    for lang, path, cols in files:
        if not os.path.exists(path):
            print(f"File not found: {path}")
            continue
        
        try:
            df = pd.read_excel(path)
            df = df.dropna(how='all')
            
            subset = df.copy()
            subset['Source File'] = os.path.basename(path)
            subset['Language'] = lang
            subset['Excel Row'] = subset.index + 2 
            
            rename_map = {
                cols['acc_no']: 'Accession Number',
                cols['title']: 'Title',
                cols['author']: 'Author',
                cols['subject']: 'Subject'
            }
            subset = subset.rename(columns=rename_map)
            
            final_cols = ['Accession Number', 'Source File', 'Language', 'Excel Row', 'Title', 'Author', 'Subject']
            subset = subset[[c for c in final_cols if c in subset.columns]]
            
            all_data.append(subset)
        except Exception as e:
            print(f"Error reading {path}: {e}")

    master_df = pd.concat(all_data, ignore_index=True)
    
    # Standardize IDs for analysis
    master_df['Clean ID'] = master_df['Accession Number'].astype(str).str.strip().str.upper()
    
    # 1. Identify Conflicts (Duplicate IDs)
    valid_ids_df = master_df[(master_df['Clean ID'] != 'NAN') & (master_df['Clean ID'] != '') & (master_df['Accession Number'].notna())]
    conflict_ids = valid_ids_df[valid_ids_df.duplicated(subset=['Clean ID'], keep=False)]['Clean ID'].unique()
    conflict_rows = valid_ids_df[valid_ids_df['Clean ID'].isin(conflict_ids)].copy()
    conflict_rows = conflict_rows.sort_values(by=['Clean ID', 'Source File'])
    
    # 2. Identify Missing IDs
    missing_ids_df = master_df[(master_df['Clean ID'] == 'NAN') | (master_df['Clean ID'] == '') | (master_df['Accession Number'].isna())].copy()
    missing_ids_df['Accession Number'] = "[MISSING]"
    
    # Building the formatted report
    formatted_list = []
    columns = ['Accession Number', 'Source File', 'Language', 'Excel Row', 'Title', 'Author', 'Subject']
    empty_row = {col: "" for col in columns}
    
    # Add Conflicts Section
    if len(conflict_ids) > 0:
        header_conflict = {col: "" for col in columns}
        header_conflict['Accession Number'] = "--- DUPLICATE ID CONFLICTS ---"
        formatted_list.append(header_conflict)
        
        groups = conflict_rows.groupby('Clean ID')
        for name, group in groups:
            for _, row in group.iterrows():
                formatted_list.append(row[columns].to_dict())
            formatted_list.append(empty_row) # Blank row between groups
    
    # Add separator
    formatted_list.append(empty_row)
    
    # Add Missing IDs Section
    if not missing_ids_df.empty:
        header_missing = {col: "" for col in columns}
        header_missing['Accession Number'] = "--- BOOKS WITH MISSING ACCESSION NUMBERS ---"
        formatted_list.append(header_missing)
        
        for _, row in missing_ids_df.iterrows():
            formatted_list.append(row[columns].to_dict())

    # Convert back to DataFrame
    formatted_df = pd.DataFrame(formatted_list)
    
    # Save to Excel
    output_path = 'migrations/Book_Migration_Conflicts.xlsx'
    formatted_df.to_excel(output_path, index=False, sheet_name='Migration Issues')

    print(f"Updated report created: {output_path}")
    print(f"Conflicts documented: {len(conflict_ids)} groups")
    print(f"Missing IDs documented: {len(missing_ids_df)} rows")

if __name__ == "__main__":
    create_formatted_conflict_report()

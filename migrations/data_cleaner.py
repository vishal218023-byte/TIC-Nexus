"""Data cleaning and validation script for Excel book data.

This script reads the Excel file, cleans and validates the data,
and prepares it for database migration.
"""
import pandas as pd
import re
import argparse
from typing import Dict, List, Tuple
from pathlib import Path


class BookDataCleaner:
    """Cleans and validates book data from Excel for database migration."""
    
    def __init__(self, excel_path: str = "migrations/TIC BOOK LIST.xlsx"):
        """Initialize the data cleaner.
        
        Args:
            excel_path: Path to the Excel file
        """
        self.excel_path = excel_path
        self.df = None
        self.cleaned_df = None
        self.validation_errors = []
        self.auto_acc_counter = 1
        
    def load_data(self) -> pd.DataFrame:
        """Load Excel data and remove empty rows.
        
        Returns:
            DataFrame with loaded data
        """
        print(f"Loading data from {self.excel_path}...")
        self.df = pd.read_excel(self.excel_path)
        
        # Remove completely empty rows
        self.df = self.df.dropna(how='all')
        
        # Remove the last row if it's all NaN (artifact from Excel)
        if self.df.iloc[-1].isna().all():
            self.df = self.df.iloc[:-1]
        
        print(f"Loaded {len(self.df)} records")
        return self.df
    
    def clean_accession_number(self, acc_no) -> str:
        """Clean and validate accession number.
        
        Args:
            acc_no: Raw accession number from Excel
            
        Returns:
            Cleaned accession number
        """
        if pd.isna(acc_no) or str(acc_no).strip() == '':
            # Generate auto accession number
            generated = f"AUTO-{self.auto_acc_counter:05d}"
            self.auto_acc_counter += 1
            return generated
        
        # Clean existing accession number
        acc_str = str(acc_no).strip().upper()
        return acc_str
    
    def convert_storage_location(self, location) -> str:
        """Convert storage location to TLC format.
        
        Converts formats like:
        - "R1 - S1" → "TLC-R-1-S-1"
        - "R13 S216" → "TLC-R-13-S-216"
        - "R3 45" → "TLC-R-3-S-45"
        
        Args:
            location: Raw storage location from Excel
            
        Returns:
            Formatted storage location
        """
        if pd.isna(location) or str(location).strip() == '':
            return "TLC-R-1-S-1"  # Default location
        
        location_str = str(location).strip().upper()
        
        # Pattern 1: Already in TLC format
        if location_str.startswith('TLC-R-'):
            return location_str
        
        # Pattern 2: "R1 - S1" or "R1 -S1" or "R1- S1" (with dash and S)
        match2 = re.search(r'R\s*(\d+)\s*-\s*S\s*(\d+)', location_str, re.IGNORECASE)
        if match2:
            rack = match2.group(1)
            shelf = match2.group(2)
            return f"TLC-R-{rack}-S-{shelf}"
        
        # Pattern 3: "R1 S1" (with S, no dash)
        match3 = re.search(r'R\s*(\d+)\s+S\s*(\d+)', location_str, re.IGNORECASE)
        if match3:
            rack = match3.group(1)
            shelf = match3.group(2)
            return f"TLC-R-{rack}-S-{shelf}"
        
        # Pattern 4: "R3 45" or "R-S38" (numbers only, assume second is shelf)
        match4 = re.search(r'R[-\s]*(\d+)\s+(\d+)', location_str, re.IGNORECASE)
        if match4:
            rack = match4.group(1)
            shelf = match4.group(2)
            return f"TLC-R-{rack}-S-{shelf}"
        
        # Pattern 5: "R-S38" format
        match5 = re.search(r'R-S(\d+)', location_str, re.IGNORECASE)
        if match5:
            shelf = match5.group(1)
            return f"TLC-R-1-S-{shelf}"
        
        # If no pattern matches, use default
        print(f"Warning: Could not parse location '{location}', using default")
        return "TLC-R-1-S-1"
    
    def clean_year(self, year) -> int | None:
        """Clean and validate publication year.
        
        Args:
            year: Raw year value from Excel
            
        Returns:
            Integer year or None
        """
        if pd.isna(year):
            return None
        
        year_str = str(year).strip()
        
        # Extract first 4-digit number
        match = re.search(r'\d{4}', year_str)
        if match:
            year_int = int(match.group())
            # Validate year range (1800-2030)
            if 1800 <= year_int <= 2030:
                return year_int
        
        return None
    
    def clean_isbn(self, isbn) -> str | None:
        """Clean ISBN number.
        
        Args:
            isbn: Raw ISBN from Excel
            
        Returns:
            Cleaned ISBN or None
        """
        if pd.isna(isbn) or str(isbn).strip() == '':
            return None
        
        isbn_str = str(isbn).strip()
        # Remove any hyphens and spaces for storage
        isbn_clean = isbn_str.replace('-', '').replace(' ', '')
        
        return isbn_clean if isbn_clean else None
    
    def clean_text_field(self, text, default: str = "") -> str:
        """Clean general text fields.
        
        Args:
            text: Raw text value
            default: Default value if empty
            
        Returns:
            Cleaned text
        """
        if pd.isna(text) or str(text).strip() == '':
            return default
        
        # Strip whitespace and normalize
        cleaned = str(text).strip()
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    def clean_all_data(self) -> pd.DataFrame:
        """Apply all cleaning operations to the dataset.
        
        Returns:
            Cleaned DataFrame
        """
        print("\nCleaning data...")
        
        if self.df is None:
            self.load_data()
        
        # Create a copy for cleaning
        self.cleaned_df = self.df.copy()
        
        # Clean each field
        print("  - Cleaning accession numbers...")
        self.cleaned_df['acc_no'] = self.cleaned_df['ACC. NO'].apply(self.clean_accession_number)
        
        print("  - Cleaning authors...")
        self.cleaned_df['author'] = self.cleaned_df['AUTHOR'].apply(
            lambda x: self.clean_text_field(x, "Unknown Author")
        )
        
        print("  - Cleaning titles...")
        self.cleaned_df['title'] = self.cleaned_df['TITLE'].apply(
            lambda x: self.clean_text_field(x, "Untitled")
        )
        
        print("  - Cleaning publisher info...")
        self.cleaned_df['publisher_info'] = self.cleaned_df['PUBLISHER / PLACE OF PUB'].apply(
            lambda x: self.clean_text_field(x, "")
        )
        
        print("  - Cleaning years...")
        self.cleaned_df['year'] = self.cleaned_df[' YEAR'].apply(self.clean_year)
        
        print("  - Cleaning ISBNs...")
        self.cleaned_df['isbn'] = self.cleaned_df['ISBN'].apply(self.clean_isbn)
        
        print("  - Converting storage locations...")
        self.cleaned_df['storage_loc'] = self.cleaned_df['RACK NO / SHELF NO'].apply(
            self.convert_storage_location
        )
        
        print("  - Cleaning subjects...")
        self.cleaned_df['subject'] = self.cleaned_df['SUBJECT'].apply(
            lambda x: self.clean_text_field(x, "General")
        )
        
        print("  - Cleaning class numbers...")
        self.cleaned_df['class_no'] = self.cleaned_df['CLASS. NO'].apply(
            lambda x: self.clean_text_field(x, "")
        )
        
        # Select only the cleaned columns we need
        self.cleaned_df = self.cleaned_df[[
            'acc_no', 'author', 'title', 'publisher_info', 
            'year', 'isbn', 'storage_loc', 'subject', 'class_no'
        ]]
        
        print(f"\nCleaned {len(self.cleaned_df)} records")
        return self.cleaned_df
    
    def handle_duplicates(self):
        """Handle duplicate accession numbers by appending suffixes.
        
        Returns:
            Number of duplicates fixed
        """
        # Find duplicates
        duplicates = self.cleaned_df[self.cleaned_df['acc_no'].duplicated(keep=False)]
        
        if len(duplicates) == 0:
            return 0
        
        print(f"\nHandling {len(duplicates)} duplicate accession numbers...")
        
        # Group by accession number
        dup_groups = self.cleaned_df.groupby('acc_no').filter(lambda x: len(x) > 1)
        
        fixed_count = 0
        for acc_no in dup_groups['acc_no'].unique():
            # Get all rows with this accession number
            mask = self.cleaned_df['acc_no'] == acc_no
            indices = self.cleaned_df[mask].index.tolist()
            
            # Keep first one, add suffix to others
            for i, idx in enumerate(indices[1:], start=2):
                old_acc = self.cleaned_df.at[idx, 'acc_no']
                new_acc = f"{old_acc}-DUP{i}"
                self.cleaned_df.at[idx, 'acc_no'] = new_acc
                fixed_count += 1
        
        print(f"  ✓ Fixed {fixed_count} duplicates by adding suffixes")
        return fixed_count
    
    def validate_data(self) -> Tuple[bool, List[str]]:
        """Validate cleaned data against database constraints.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        print("\nValidating data...")
        errors = []
        
        if self.cleaned_df is None:
            errors.append("No cleaned data available. Run clean_all_data() first.")
            return False, errors
        
        # Check for duplicate accession numbers
        duplicates = self.cleaned_df[self.cleaned_df['acc_no'].duplicated(keep=False)]
        if len(duplicates) > 0:
            errors.append(f"Found {len(duplicates)} duplicate accession numbers")
            print(f"  ✗ Duplicate accession numbers: {len(duplicates)}")
        else:
            print("  ✓ No duplicate accession numbers")
        
        # Validate storage location format
        invalid_locs = self.cleaned_df[
            ~self.cleaned_df['storage_loc'].str.match(r'^TLC-R-\d+-S-\d+$')
        ]
        if len(invalid_locs) > 0:
            errors.append(f"Found {len(invalid_locs)} invalid storage locations")
            print(f"  ✗ Invalid storage locations: {len(invalid_locs)}")
        else:
            print("  ✓ All storage locations valid")
        
        # Check for required fields
        missing_title = self.cleaned_df[self.cleaned_df['title'] == 'Untitled']
        if len(missing_title) > 0:
            print(f"  ⚠ Warning: {len(missing_title)} books with no title")
        
        missing_author = self.cleaned_df[self.cleaned_df['author'] == 'Unknown Author']
        if len(missing_author) > 0:
            print(f"  ⚠ Warning: {len(missing_author)} books with unknown author")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_statistics(self) -> Dict:
        """Generate statistics about the cleaned data.
        
        Returns:
            Dictionary of statistics
        """
        if self.cleaned_df is None:
            return {}
        
        stats = {
            'total_records': len(self.cleaned_df),
            'auto_generated_acc_no': len(self.cleaned_df[self.cleaned_df['acc_no'].str.startswith('AUTO-')]),
            'books_with_isbn': len(self.cleaned_df[self.cleaned_df['isbn'].notna()]),
            'books_with_year': len(self.cleaned_df[self.cleaned_df['year'].notna()]),
            'books_with_publisher': len(self.cleaned_df[self.cleaned_df['publisher_info'] != '']),
            'unique_subjects': self.cleaned_df['subject'].nunique(),
            'unique_racks': self.cleaned_df['storage_loc'].str.extract(r'TLC-R-(\d+)-')[0].nunique(),
        }
        
        return stats
    
    def preview_sample(self, n: int = 10):
        """Print a sample of cleaned data.
        
        Args:
            n: Number of records to display
        """
        if self.cleaned_df is None:
            print("No cleaned data available.")
            return
        
        print(f"\n{'='*80}")
        print(f"SAMPLE DATA (First {n} records)")
        print(f"{'='*80}\n")
        
        for idx, row in self.cleaned_df.head(n).iterrows():
            print(f"Record {idx + 1}:")
            print(f"  Acc No:    {row['acc_no']}")
            print(f"  Title:     {row['title'][:60]}...")
            print(f"  Author:    {row['author']}")
            print(f"  Publisher: {row['publisher_info'][:50] if row['publisher_info'] else 'N/A'}")
            print(f"  Year:      {row['year'] if pd.notna(row['year']) else 'N/A'}")
            print(f"  ISBN:      {row['isbn'] if pd.notna(row['isbn']) else 'N/A'}")
            print(f"  Location:  {row['storage_loc']}")
            print(f"  Subject:   {row['subject']}")
            print(f"  Class No:  {row['class_no'] if row['class_no'] else 'N/A'}")
            print()
    
    def save_cleaned_data(self, output_path: str = "migrations/cleaned_books.csv"):
        """Save cleaned data to CSV for inspection.
        
        Args:
            output_path: Path to save CSV file
        """
        if self.cleaned_df is None:
            print("No cleaned data to save.")
            return
        
        self.cleaned_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\nCleaned data saved to: {output_path}")
    
    def run_full_cleaning(self, preview: bool = True) -> pd.DataFrame:
        """Run complete cleaning pipeline.
        
        Args:
            preview: Whether to show preview and statistics
            
        Returns:
            Cleaned DataFrame
        """
        print("="*80)
        print("BOOK DATA CLEANING PIPELINE")
        print("="*80)
        
        # Step 1: Load
        self.load_data()
        
        # Step 2: Clean
        self.clean_all_data()
        
        # Step 3: Handle duplicates
        self.handle_duplicates()
        
        # Step 4: Validate
        is_valid, errors = self.validate_data()
        
        # Step 4: Statistics
        if preview:
            stats = self.get_statistics()
            print("\n" + "="*80)
            print("STATISTICS")
            print("="*80)
            for key, value in stats.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
            
            # Show sample
            self.preview_sample(5)
        
        # Step 5: Save
        self.save_cleaned_data()
        
        if not is_valid:
            print("\n⚠ VALIDATION ERRORS:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✓ Data validation passed!")
        
        return self.cleaned_df


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Clean and validate book data from Excel')
    parser.add_argument('--preview', action='store_true', help='Show preview and statistics')
    parser.add_argument('--no-save', action='store_true', help='Do not save cleaned CSV')
    parser.add_argument('--sample', type=int, default=5, help='Number of sample records to show')
    
    args = parser.parse_args()
    
    cleaner = BookDataCleaner()
    cleaned_df = cleaner.run_full_cleaning(preview=args.preview)
    
    if args.preview:
        print("\n" + "="*80)
        print("READY FOR MIGRATION")
        print("="*80)
        print(f"✓ {len(cleaned_df)} books ready to migrate")
        print("\nNext step: Run migration script")
        print("  python migrations/migrate_books.py --dry-run")


if __name__ == "__main__":
    main()

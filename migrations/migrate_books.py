"""Database migration script for importing books from Excel.

This script takes the cleaned book data and imports it into the
TLC Nexus database with proper error handling and validation.
"""
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.database import SessionLocal, engine
from app.models import Book, Base
from migrations.data_cleaner import BookDataCleaner


class BookMigrator:
    """Handles migration of book data from Excel to database."""
    
    def __init__(self, dry_run: bool = False):
        """Initialize the migrator.
        
        Args:
            dry_run: If True, simulate migration without database changes
        """
        self.dry_run = dry_run
        self.db: Session = None
        self.stats = {
            'total_records': 0,
            'successful': 0,
            'skipped': 0,
            'errors': 0,
            'duplicates': 0
        }
        self.error_log = []
        
    def connect_db(self) -> Session:
        """Connect to the database.
        
        Returns:
            Database session
        """
        if not self.dry_run:
            print("Connecting to database...")
            self.db = SessionLocal()
            print("✓ Database connected")
        else:
            print("DRY RUN MODE - No database connection")
            self.db = None
        
        return self.db
    
    def close_db(self):
        """Close database connection."""
        if self.db:
            self.db.close()
            print("Database connection closed")
    
    def check_existing_book(self, acc_no: str) -> bool:
        """Check if a book with given accession number already exists.
        
        Args:
            acc_no: Accession number to check
            
        Returns:
            True if book exists, False otherwise
        """
        if self.dry_run:
            return False
        
        existing = self.db.query(Book).filter(Book.acc_no == acc_no).first()
        return existing is not None
    
    def create_book_from_row(self, row: pd.Series) -> Book:
        """Create a Book model instance from a DataFrame row.
        
        Args:
            row: DataFrame row with cleaned book data
            
        Returns:
            Book model instance
        """
        book = Book(
            acc_no=row['acc_no'],
            author=row['author'],
            title=row['title'],
            publisher_info=row['publisher_info'] if row['publisher_info'] else None,
            subject=row['subject'],
            class_no=row['class_no'] if row['class_no'] else None,
            year=int(row['year']) if pd.notna(row['year']) else None,
            isbn=row['isbn'] if pd.notna(row['isbn']) else None,
            storage_loc=row['storage_loc'],
            is_issued=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return book
    
    def migrate_book(self, row: pd.Series, index: int) -> Tuple[bool, str]:
        """Migrate a single book record.
        
        Args:
            row: DataFrame row with book data
            index: Row index for logging
            
        Returns:
            Tuple of (success, message)
        """
        acc_no = row['acc_no']
        
        # Check for duplicates
        if not self.dry_run and self.check_existing_book(acc_no):
            self.stats['duplicates'] += 1
            return False, f"Duplicate accession number: {acc_no}"
        
        try:
            # Create book instance
            book = self.create_book_from_row(row)
            
            if not self.dry_run:
                # Add to database
                self.db.add(book)
                self.db.flush()  # Flush but don't commit yet
            
            self.stats['successful'] += 1
            return True, f"Successfully migrated: {acc_no}"
            
        except IntegrityError as e:
            self.stats['errors'] += 1
            error_msg = f"Integrity error for {acc_no}: {str(e)}"
            self.error_log.append(error_msg)
            return False, error_msg
            
        except Exception as e:
            self.stats['errors'] += 1
            error_msg = f"Error migrating {acc_no}: {str(e)}"
            self.error_log.append(error_msg)
            return False, error_msg
    
    def migrate_batch(self, df: pd.DataFrame, batch_size: int = 100) -> Dict:
        """Migrate books in batches for better performance.
        
        Args:
            df: DataFrame with cleaned book data
            batch_size: Number of records per batch
            
        Returns:
            Dictionary with migration statistics
        """
        self.stats['total_records'] = len(df)
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        print(f"\nMigrating {len(df)} books in {total_batches} batches...")
        print(f"Batch size: {batch_size}")
        print("="*80)
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]
            
            print(f"\nBatch {batch_num + 1}/{total_batches} (Records {start_idx + 1}-{end_idx})")
            
            for idx, row in batch_df.iterrows():
                success, message = self.migrate_book(row, idx)
                
                # Print progress every 20 records
                if (idx + 1) % 20 == 0:
                    print(f"  Processed {idx + 1}/{len(df)} records...")
            
            # Commit batch if not dry run
            if not self.dry_run:
                try:
                    self.db.commit()
                    print(f"  ✓ Batch {batch_num + 1} committed")
                except SQLAlchemyError as e:
                    self.db.rollback()
                    print(f"  ✗ Batch {batch_num + 1} rolled back: {str(e)}")
                    self.stats['errors'] += len(batch_df)
        
        return self.stats
    
    def print_summary(self):
        """Print migration summary."""
        print("\n" + "="*80)
        print("MIGRATION SUMMARY")
        print("="*80)
        print(f"Total Records:     {self.stats['total_records']}")
        print(f"Successful:        {self.stats['successful']} ✓")
        print(f"Duplicates:        {self.stats['duplicates']} (skipped)")
        print(f"Errors:            {self.stats['errors']} ✗")
        print(f"Success Rate:      {self.stats['successful']/self.stats['total_records']*100:.2f}%")
        
        if self.error_log:
            print(f"\n{'='*80}")
            print(f"ERRORS ({len(self.error_log)})")
            print(f"{'='*80}")
            for error in self.error_log[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.error_log) > 10:
                print(f"  ... and {len(self.error_log) - 10} more errors")
    
    def save_report(self, output_path: str = "migrations/migration_report.txt"):
        """Save migration report to file.
        
        Args:
            output_path: Path to save report
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("TLC NEXUS - BOOK MIGRATION REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}\n")
            f.write("\n")
            
            f.write("STATISTICS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Records:     {self.stats['total_records']}\n")
            f.write(f"Successful:        {self.stats['successful']}\n")
            f.write(f"Duplicates:        {self.stats['duplicates']}\n")
            f.write(f"Errors:            {self.stats['errors']}\n")
            f.write(f"Success Rate:      {self.stats['successful']/self.stats['total_records']*100:.2f}%\n")
            f.write("\n")
            
            if self.error_log:
                f.write("ERRORS\n")
                f.write("-"*80 + "\n")
                for error in self.error_log:
                    f.write(f"  - {error}\n")
        
        print(f"\nReport saved to: {output_path}")
    
    def run_migration(self, cleaned_data_path: str = None) -> Dict:
        """Run the complete migration process.
        
        Args:
            cleaned_data_path: Path to cleaned CSV file (optional)
            
        Returns:
            Dictionary with migration statistics
        """
        print("="*80)
        print("BOOK MIGRATION TO DATABASE")
        print("="*80)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        print()
        
        # Step 1: Load cleaned data
        if cleaned_data_path and Path(cleaned_data_path).exists():
            print(f"Loading cleaned data from {cleaned_data_path}...")
            df = pd.read_csv(cleaned_data_path)
        else:
            print("Running data cleaner first...")
            cleaner = BookDataCleaner()
            df = cleaner.run_full_cleaning(preview=False)
        
        print(f"Loaded {len(df)} records\n")
        
        # Step 2: Connect to database
        self.connect_db()
        
        try:
            # Step 3: Migrate data
            self.migrate_batch(df, batch_size=100)
            
            # Step 4: Print summary
            self.print_summary()
            
            # Step 5: Save report
            self.save_report()
            
            if self.dry_run:
                print("\n" + "="*80)
                print("DRY RUN COMPLETE - No changes made to database")
                print("="*80)
                print("\nTo execute migration, run:")
                print("  python migrations/migrate_books.py --execute")
            else:
                print("\n" + "="*80)
                print("MIGRATION COMPLETE")
                print("="*80)
                print(f"\n✓ {self.stats['successful']} books added to database")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            if not self.dry_run and self.db:
                self.db.rollback()
                print("Database rolled back")
            raise
        
        finally:
            # Step 6: Close database
            self.close_db()
        
        return self.stats


def verify_database_connection() -> bool:
    """Verify database connection and schema.
    
    Returns:
        True if connection successful
    """
    try:
        db = SessionLocal()
        # Check if Book table exists
        book_count = db.query(Book).count()
        print(f"✓ Database connection verified")
        print(f"  Current books in database: {book_count}")
        db.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        return False


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description='Migrate book data from Excel to database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (no database changes)
  python migrations/migrate_books.py --dry-run
  
  # Execute migration
  python migrations/migrate_books.py --execute
  
  # Use pre-cleaned CSV
  python migrations/migrate_books.py --execute --csv migrations/cleaned_books.csv
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without making database changes'
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute the migration (makes database changes)'
    )
    
    parser.add_argument(
        '--csv',
        type=str,
        help='Path to pre-cleaned CSV file (optional)'
    )
    
    args = parser.parse_args()
    
    # Check that either dry-run or execute is specified
    if not args.dry_run and not args.execute:
        parser.print_help()
        print("\n⚠ ERROR: You must specify either --dry-run or --execute")
        sys.exit(1)
    
    # Verify database connection first
    if args.execute:
        print("Verifying database connection...")
        if not verify_database_connection():
            print("\n✗ Cannot proceed with migration")
            sys.exit(1)
        print()
    
    # Run migration
    migrator = BookMigrator(dry_run=args.dry_run)
    try:
        stats = migrator.run_migration(cleaned_data_path=args.csv)
        sys.exit(0 if stats['errors'] == 0 else 1)
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Migration failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

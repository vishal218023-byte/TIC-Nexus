# TIC Nexus - Excel Data Migration

## Overview
This folder contains the Excel data migration scripts and files for importing book inventory data into the TIC Nexus database.

## Source Data
- **File**: `TIC BOOK LIST.xlsx`
- **Total Records**: ~6,216 books (after cleaning empty rows)
- **Original Excel Format**: 11 columns with library catalog data

## Excel Column Mapping to Database

| Excel Column | Database Field | Notes |
|--------------|----------------|-------|
| SL.NO | - | Serial number (not stored) |
| ACC. NO | `acc_no` | Accession number (unique identifier) |
| AUTHOR | `author` | Book author(s) |
| TITLE | `title` | Book title |
| PUBLISHER / PLACE OF PUB | `publisher_info` | Publisher and location |
| YEAR | `year` | Publication year (needs cleaning) |
| ISBN | `isbn` | ISBN number |
| RACK NO / SHELF NO | `storage_loc` | Storage location (needs format conversion) |
| SUBJECT | `subject` | Subject category |
| CLASS. NO | `class_no` | Classification number |
| Unnamed: 10 | - | Empty column (ignored) |

## Data Quality Issues Identified

### 1. Missing Accession Numbers (~215 records)
- **Issue**: Some books don't have ACC. NO
- **Solution**: Generate unique accession numbers (e.g., AUTO-0001, AUTO-0002)

### 2. Storage Location Format Mismatch
- **Excel Format**: "R1 - S1", "R13 S216"
- **Database Format**: "TIC-R-1-S-1"
- **Solution**: Convert to standardized format

### 3. Missing Data
- **Author**: 369 missing → Use "Unknown Author"
- **Publisher**: 433 missing → Use empty string or "Unknown"
- **Year**: 555 missing → Set to NULL
- **ISBN**: 2,167 missing → Set to NULL

### 4. Year Data Type Issues
- Some years are objects/strings
- Need to convert to integers

## Migration Strategy

### Phase 1: Data Cleaning & Validation
1. Load Excel file with pandas
2. Drop completely empty rows
3. Clean and standardize data:
   - Generate ACC. NO for missing entries
   - Convert storage location format
   - Clean year data (extract numeric values)
   - Handle missing/null values
   - Trim whitespace from all text fields

### Phase 2: Database Schema Alignment
1. Map Excel columns to Book model fields
2. Validate data against database constraints:
   - Unique accession numbers
   - Storage location format (regex: `^TIC-R-\d+-S-\d+$`)
   - ISBN format (if present)
   - Year range validation

### Phase 3: Migration Execution
1. Connect to database
2. Check for existing books (avoid duplicates)
3. Batch insert cleaned records
4. Set `is_issued` to False for all books
5. Log any errors or skipped records

### Phase 4: Validation
1. Verify record counts
2. Check data integrity
3. Generate migration report

## Files in This Folder

- `TIC BOOK LIST.xlsx` - Original Excel data source
- `data_cleaner.py` - Data cleaning and validation script
- `migrate_books.py` - Main migration script
- `migration_report.txt` - Post-migration report (generated after run)
- `README.md` - This file

## Usage

### Step 1: Clean and Preview Data
```bash
python migrations/data_cleaner.py --preview
```

### Step 2: Run Migration (Dry Run)
```bash
python migrations/migrate_books.py --dry-run
```

### Step 3: Execute Migration
```bash
python migrations/migrate_books.py --execute
```

### Step 4: Review Report
```bash
cat migrations/migration_report.txt
```

## Safety Features

1. **Dry Run Mode**: Test migration without database changes
2. **Duplicate Detection**: Skip books with existing accession numbers
3. **Error Logging**: All errors logged to migration_report.txt
4. **Rollback Option**: Can be reversed by database restore
5. **Validation Checks**: Pre-migration validation of all data

## Post-Migration Tasks

- [ ] Verify total book count matches Excel records
- [ ] Spot-check random books for data accuracy
- [ ] Test book search functionality
- [ ] Verify storage location format
- [ ] Update dashboard statistics

## Notes

- All books imported with `is_issued = False`
- Created/updated timestamps set to migration time
- No transaction history imported (only physical inventory)
- Digital books not affected by this migration

---
**Last Updated**: 2026-02-04
**Migration Status**: Pending

@echo off
REM Batch script to run the complete migration process

echo ================================================================================
echo TLC NEXUS - BOOK DATA MIGRATION
echo ================================================================================
echo.

echo Step 1: Data Cleaning and Validation
echo ================================================================================
python migrations/data_cleaner.py --preview
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Data cleaning failed!
    pause
    exit /b 1
)

echo.
echo.
echo Step 2: Dry Run Migration (Preview)
echo ================================================================================
python migrations/migrate_books.py --dry-run
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Dry run failed!
    pause
    exit /b 1
)

echo.
echo.
echo ================================================================================
echo Ready to Execute Migration
echo ================================================================================
echo The dry run completed successfully.
echo.
set /p confirm="Do you want to execute the LIVE migration? (yes/no): "

if /i "%confirm%"=="yes" (
    echo.
    echo Step 3: Executing Live Migration
    echo ================================================================================
    python migrations/migrate_books.py --execute
    
    if %errorlevel% equ 0 (
        echo.
        echo ================================================================================
        echo MIGRATION COMPLETED SUCCESSFULLY!
        echo ================================================================================
        echo.
        echo Check the report: migrations/migration_report.txt
        echo.
    ) else (
        echo.
        echo ERROR: Migration failed!
        echo Check the report for details: migrations/migration_report.txt
    )
) else (
    echo.
    echo Migration cancelled by user.
)

echo.
pause

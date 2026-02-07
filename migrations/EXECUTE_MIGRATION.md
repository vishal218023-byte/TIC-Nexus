# Execute Migration - Quick Start Guide

## ✅ Pre-Flight Checklist

Before executing the migration, ensure:

- [ ] **Backup Database**: Copy `data/tic_nexus.db` to a safe location
- [ ] **Stop Application**: Close TIC Nexus if running
- [ ] **Free Disk Space**: Ensure at least 100MB free space
- [ ] **Review Dry Run**: Confirmed 100% success rate

---

## 🚀 Execute Migration (Choose One Method)

### Method 1: Automated (Recommended) ⭐

Simply run the batch script:

```bash
migrations\run_migration.bat
```

This will:
1. ✓ Run data cleaning
2. ✓ Show preview and statistics
3. ✓ Run dry-run migration
4. ⚠️ **Ask for your confirmation**
5. ✓ Execute live migration (if you confirm)

**Estimated Time**: 2-3 minutes

---

### Method 2: Manual Execution

If you prefer step-by-step control:

#### Step 1: Execute Migration
```bash
python migrations/migrate_books.py --execute
```

#### Step 2: Monitor Progress
Watch for:
- Batch processing messages
- Progress updates (every 20 records)
- Success/error counts

#### Step 3: Review Results
```bash
type migrations\migration_report.txt
```

**Estimated Time**: 2-3 minutes

---

## 📊 What to Expect

### During Migration

```
================================================================================
BOOK MIGRATION TO DATABASE
================================================================================
Mode: LIVE MIGRATION

Loading cleaned data from migrations/cleaned_books.csv...
Loaded 6216 records

Connecting to database...
✓ Database connected

Migrating 6216 books in 63 batches...
Batch size: 100
================================================================================

Batch 1/63 (Records 1-100)
  Processed 20/6216 records...
  Processed 40/6216 records...
  ...
  ✓ Batch 1 committed

[... continues through all 63 batches ...]

================================================================================
MIGRATION SUMMARY
================================================================================
Total Records:     6216
Successful:        6216 ✓
Duplicates:        0 (skipped)
Errors:            0 ✗
Success Rate:      100.00%

Report saved to: migrations/migration_report.txt

================================================================================
MIGRATION COMPLETE
================================================================================

✓ 6216 books added to database
```

---

## ✅ Post-Migration Verification

### 1. Check Record Count
```bash
python -c "from app.database import SessionLocal; from app.models import Book; db = SessionLocal(); print(f'Total books: {db.query(Book).count()}'); db.close()"
```

**Expected**: Should show your existing books + 6,216 new books

### 2. Verify Sample Records
Open the application and check:
- Search for a book (e.g., "Radio")
- Check book details display correctly
- Verify storage locations show as "TIC-R-X-S-Y"

### 3. Test Functionality
- [ ] Book search works
- [ ] Book details display correctly
- [ ] Dashboard statistics updated
- [ ] Inventory page loads all books
- [ ] Storage locations are correct

### 4. Review Migration Report
Check `migrations/migration_report.txt` for:
- Final statistics
- Any errors (should be 0)
- Duplicate handling (should be 0)

---

## ⚠️ If Something Goes Wrong

### Problem: Migration fails with database error
**Solution**:
```bash
# The script will automatically rollback the current batch
# Check migrations/migration_report.txt for error details
# Fix the issue and re-run migration
```

### Problem: Some records failed
**Solution**:
```bash
# Check migration_report.txt for specific errors
# Failed records will be listed with reasons
# You can manually add them later or fix and re-run
```

### Problem: Need to rollback everything
**Solution**:
```bash
# Stop application
# Restore from backup
copy backup_tic_nexus.db data\tic_nexus.db
# Restart application
```

---

## 📈 Success Criteria

Migration is successful when:

- ✅ Migration report shows 100% success rate
- ✅ All 6,216 books added to database
- ✅ 0 errors in migration report
- ✅ Book search returns results
- ✅ Dashboard statistics updated
- ✅ All storage locations in correct format

---

## 🎉 After Successful Migration

1. **Keep Migration Files**: Don't delete the migrations folder (for reference)
2. **Update Documentation**: Note the migration date in your records
3. **Test Thoroughly**: Use the application normally for a few operations
4. **Monitor**: Watch for any data issues in the first few days

---

## 📞 Need Help?

- **Documentation**: See `migrations/README.md` for detailed info
- **Migration Plan**: See `migrations/MIGRATION_PLAN.md` for overview
- **Error Report**: Check `migrations/migration_report.txt` for errors

---

## 🚀 Ready to Execute?

When you're ready:

1. **Backup your database** (IMPORTANT!)
2. **Close the application**
3. **Run**: `migrations\run_migration.bat`
4. **Wait**: 2-3 minutes for completion
5. **Verify**: Check results and test application

**Good luck! 🍀**

---
*Last Updated: 2026-02-04*

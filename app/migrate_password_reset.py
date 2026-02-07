"""Database migration script to add password reset tables.

This script creates the new tables for password reset functionality:
- password_reset_tokens
- password_history

Run this script once to add the new tables to the existing database.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import PasswordResetToken, PasswordHistory

def run_migration():
    """Create password reset tables."""
    print("=" * 60)
    print("TLC Nexus - Password Reset Tables Migration")
    print("=" * 60)
    print()
    
    try:
        # Create only the password reset tables
        print("Creating password_reset_tokens table...")
        PasswordResetToken.__table__.create(engine, checkfirst=True)
        print("✓ password_reset_tokens table created successfully")
        
        print("\nCreating password_history table...")
        PasswordHistory.__table__.create(engine, checkfirst=True)
        print("✓ password_history table created successfully")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print("\nPassword reset functionality is now ready to use.")
        print("\nNext steps:")
        print("1. Restart the application")
        print("2. Login as admin")
        print("3. Go to User Management to generate reset tokens")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        print("\nPlease check the error and try again.")
        sys.exit(1)

if __name__ == "__main__":
    print("\n⚠️  This will add new tables to your database.")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        run_migration()
    else:
        print("\nMigration cancelled.")

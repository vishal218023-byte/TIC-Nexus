"""
Emergency Admin Password Reset Script
======================================
This script resets the admin user's password to 'admin123'.
Use this only when the admin password is forgotten.

Usage:
    Interactive mode (with confirmations):
        python reset_admin_password.py
    
    Non-interactive mode (auto-confirm):
        python reset_admin_password.py --force
    
    Help:
        python reset_admin_password.py --help

Features:
    - Resets admin password to 'admin123'
    - Activates user if inactive
    - Shows all available users if admin not found
    - Interactive confirmations (can be skipped with --force)
    - Detailed success/error messages

Security Note:
    After using this script, login immediately and change the password
    to something secure using the Change Password feature in the sidebar.
    
Example:
    1. Run: python reset_admin_password.py --force
    2. Login with username: admin, password: admin123
    3. Click "Change Password" in sidebar
    4. Set a strong, secure password
"""

import sys
import argparse
import bcrypt
from app.database import SessionLocal
from app.models import User


def reset_admin_password(force=False):
    """Reset admin password to 'admin123'.
    
    Args:
        force: If True, skip interactive prompts
    """
    db = SessionLocal()
    
    try:
        # Find admin user (assuming username is 'admin')
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            print("❌ Error: Admin user not found!")
            print("   Looking for user with username 'admin'")
            
            # Show all users
            all_users = db.query(User).all()
            if all_users:
                print("\n📋 Available users:")
                for user in all_users:
                    print(f"   - {user.username} (ID: {user.id}, Role: {user.role})")
                
                # Ask if they want to reset a different user
                print("\n💡 Tip: You can modify this script to reset a different username")
            else:
                print("\n❌ No users found in the database!")
            
            return False
        
        # Check if user is admin role
        if admin.role != "admin":
            print(f"⚠️  Warning: User '{admin.username}' has role '{admin.role}', not 'admin'")
            if not force:
                response = input("Do you want to continue anyway? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    print("❌ Operation cancelled")
                    return False
            else:
                print("   Continuing anyway (--force mode)")
        
        # Check if user is active
        if not admin.is_active:
            print(f"⚠️  Warning: User '{admin.username}' is marked as inactive")
            if not force:
                response = input("Do you want to activate the user? (yes/no): ")
                if response.lower() in ['yes', 'y']:
                    admin.is_active = True
                    print("✅ User activated")
            else:
                admin.is_active = True
                print("✅ User activated (--force mode)")
        
        # Reset password
        new_password = "admin123"
        # Hash password directly using bcrypt to avoid passlib compatibility issues
        password_bytes = new_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        admin.hashed_password = hashed.decode('utf-8')
        
        db.commit()
        
        print("\n" + "="*60)
        print("✅ SUCCESS! Admin password has been reset")
        print("="*60)
        print(f"\n📝 Login Credentials:")
        print(f"   Username: {admin.username}")
        print(f"   Password: {new_password}")
        print(f"\n⚠️  IMPORTANT SECURITY NOTICE:")
        print(f"   1. Login immediately using the credentials above")
        print(f"   2. Go to the sidebar and click 'Change Password'")
        print(f"   3. Change to a strong, secure password")
        print(f"   4. Do NOT share these credentials")
        print("\n" + "="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error resetting password: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Emergency Admin Password Reset Script",
        epilog="Use --force to skip all interactive prompts"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip interactive prompts and force reset'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🔐 EMERGENCY ADMIN PASSWORD RESET")
    print("="*60)
    print("\nThis will reset the admin password to 'admin123'")
    print("\n⚠️  WARNING: This is a security-sensitive operation!")
    print("   Only use this if you have forgotten the admin password.")
    
    if not args.force:
        try:
            response = input("\nDo you want to continue? (yes/no): ")
            
            if response.lower() not in ['yes', 'y']:
                print("\n❌ Operation cancelled")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\n\n❌ Operation cancelled")
            sys.exit(0)
    else:
        print("\n⚡ Running in FORCE mode - skipping confirmations")
    
    print("\n🔄 Resetting password...")
    
    success = reset_admin_password(force=args.force)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

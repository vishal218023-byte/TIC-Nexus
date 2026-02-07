"""Password validation and utility functions."""
import re
import secrets
import string
from datetime import datetime, timedelta
from typing import Tuple, List
from sqlalchemy.orm import Session
from app.models import PasswordHistory, User
from app.auth import pwd_context


# Configuration
PASSWORD_RESET_CONFIG = {
    "TOKEN_LENGTH": 8,
    "TOKEN_EXPIRY_MINUTES": 60,
    "PASSWORD_HISTORY_COUNT": 3,
    "MIN_PASSWORD_LENGTH": 8,
    "REQUIRE_PASSWORD_COMPLEXITY": True,
}


def generate_reset_token(length: int = None) -> str:
    """Generate a cryptographically secure random token.
    
    Args:
        length: Token length (default from config)
    
    Returns:
        Alphanumeric token (uppercase letters and digits)
    """
    if length is None:
        length = PASSWORD_RESET_CONFIG["TOKEN_LENGTH"]
    
    # Use only uppercase letters and digits for easy reading/typing
    alphabet = string.ascii_uppercase + string.digits
    # Remove similar looking characters to avoid confusion
    alphabet = alphabet.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
    
    token = ''.join(secrets.choice(alphabet) for _ in range(length))
    return token


def calculate_token_expiry() -> datetime:
    """Calculate token expiration time.
    
    Returns:
        DateTime when token expires
    """
    expiry_minutes = PASSWORD_RESET_CONFIG["TOKEN_EXPIRY_MINUTES"]
    return datetime.utcnow() + timedelta(minutes=expiry_minutes)


def validate_password_strength(password: str) -> Tuple[bool, int, List[str]]:
    """Validate password strength and provide feedback.
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, score, feedback_messages)
        - is_valid: Boolean indicating if password meets minimum requirements
        - score: Integer 0-100 indicating password strength
        - feedback: List of feedback messages
    """
    feedback = []
    score = 0
    is_valid = True
    
    # Check minimum length
    min_length = PASSWORD_RESET_CONFIG["MIN_PASSWORD_LENGTH"]
    if len(password) < min_length:
        feedback.append(f"Password must be at least {min_length} characters long")
        is_valid = False
    else:
        score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
    
    # Check for letters
    has_letters = bool(re.search(r'[a-zA-Z]', password))
    if not has_letters:
        feedback.append("Password must contain at least one letter")
        is_valid = False
    else:
        score += 15
    
    # Check for digits
    has_digits = bool(re.search(r'\d', password))
    if not has_digits:
        feedback.append("Password must contain at least one number")
        is_valid = False
    else:
        score += 15
    
    # Additional complexity checks (optional but recommended)
    if PASSWORD_RESET_CONFIG["REQUIRE_PASSWORD_COMPLEXITY"]:
        # Check for uppercase
        has_uppercase = bool(re.search(r'[A-Z]', password))
        if has_uppercase:
            score += 10
        else:
            feedback.append("Consider adding uppercase letters for stronger password")
        
        # Check for lowercase
        has_lowercase = bool(re.search(r'[a-z]', password))
        if has_lowercase:
            score += 10
        else:
            feedback.append("Consider adding lowercase letters for stronger password")
        
        # Check for special characters
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        if has_special:
            score += 20
        else:
            feedback.append("Consider adding special characters (!@#$%^&*) for stronger password")
    
    # Check for common patterns
    common_patterns = [
        (r'(.)\1{2,}', "Avoid repeating characters (e.g., 'aaa')"),
        (r'12345|23456|34567', "Avoid sequential numbers"),
        (r'abcde|bcdef|cdefg', "Avoid sequential letters"),
        (r'password|qwerty|admin', "Avoid common words like 'password' or 'admin'"),
    ]
    
    for pattern, message in common_patterns:
        if re.search(pattern, password.lower()):
            feedback.append(message)
            score = max(0, score - 15)
    
    # Ensure score is within 0-100
    score = max(0, min(100, score))
    
    # If valid and no negative feedback, add positive message
    if is_valid and score >= 70:
        feedback = ["Strong password!"] if not feedback else feedback
    elif is_valid and score >= 50:
        feedback = ["Good password"] if not feedback else feedback
    elif is_valid:
        feedback = ["Password meets minimum requirements"] if not feedback else feedback
    
    return is_valid, score, feedback


def get_password_strength_label(score: int) -> str:
    """Get human-readable strength label from score.
    
    Args:
        score: Password strength score (0-100)
    
    Returns:
        String label: "weak", "medium", or "strong"
    """
    if score >= 70:
        return "strong"
    elif score >= 50:
        return "medium"
    else:
        return "weak"


def check_password_history(db: Session, user_id: int, new_password: str) -> bool:
    """Check if password was used recently.
    
    Args:
        db: Database session
        user_id: User ID
        new_password: New password to check
    
    Returns:
        True if password is acceptable (not in recent history), False otherwise
    """
    import bcrypt
    history_count = PASSWORD_RESET_CONFIG["PASSWORD_HISTORY_COUNT"]
    
    # Get recent password history
    recent_passwords = db.query(PasswordHistory).filter(
        PasswordHistory.user_id == user_id
    ).order_by(PasswordHistory.changed_at.desc()).limit(history_count).all()
    
    # Check if new password matches any recent passwords
    for history_entry in recent_passwords:
        try:
            password_bytes = new_password.encode('utf-8')
            hashed_bytes = history_entry.hashed_password.encode('utf-8')
            if bcrypt.checkpw(password_bytes, hashed_bytes):
                return False
        except:
            # Fallback to passlib for old hashes
            try:
                if pwd_context.verify(new_password, history_entry.hashed_password):
                    return False
            except:
                pass
    
    return True


def add_to_password_history(
    db: Session,
    user_id: int,
    hashed_password: str,
    changed_by: int = None,
    change_reason: str = "user_change",
    ip_address: str = None
) -> None:
    """Add password to history.
    
    Args:
        db: Database session
        user_id: User ID
        hashed_password: Hashed password to store
        changed_by: User ID who made the change (None if self)
        change_reason: Reason for change
        ip_address: IP address of request
    """
    history_entry = PasswordHistory(
        user_id=user_id,
        hashed_password=hashed_password,
        changed_by=changed_by if changed_by != user_id else None,
        change_reason=change_reason,
        ip_address=ip_address
    )
    db.add(history_entry)
    db.commit()


def update_user_password(
    db: Session,
    user: User,
    new_password: str,
    changed_by: int = None,
    change_reason: str = "user_change",
    ip_address: str = None
) -> Tuple[bool, str]:
    """Update user password with validation and history tracking.
    
    Args:
        db: Database session
        user: User object
        new_password: New password (plain text)
        changed_by: User ID who made the change
        change_reason: Reason for change
        ip_address: IP address of request
    
    Returns:
        Tuple of (success, message)
    """
    # Validate password strength
    is_valid, score, feedback = validate_password_strength(new_password)
    if not is_valid:
        return False, "; ".join(feedback)
    
    # Check password history
    if not check_password_history(db, user.id, new_password):
        history_count = PASSWORD_RESET_CONFIG["PASSWORD_HISTORY_COUNT"]
        return False, f"Cannot reuse any of your last {history_count} passwords"
    
    # Hash new password
    from app.auth import get_password_hash
    new_hashed_password = get_password_hash(new_password)
    
    # Update user password
    user.hashed_password = new_hashed_password
    db.commit()
    
    # Add to password history
    add_to_password_history(
        db=db,
        user_id=user.id,
        hashed_password=new_hashed_password,
        changed_by=changed_by,
        change_reason=change_reason,
        ip_address=ip_address
    )
    
    return True, "Password updated successfully"

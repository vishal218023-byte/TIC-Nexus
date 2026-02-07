"""Password reset API routes and logic."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, PasswordResetToken
from app.schemas import (
    PasswordResetTokenGenerate,
    PasswordResetTokenResponse,
    PasswordResetWithToken,
    PasswordChange,
    PasswordStrengthResponse,
    UserResponse
)
from app.auth import get_current_user, get_current_admin_user, verify_password
from app.password_utils import (
    generate_reset_token,
    calculate_token_expiry,
    validate_password_strength,
    get_password_strength_label,
    update_user_password,
)

router = APIRouter(prefix="/api/auth", tags=["password-reset"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/admin/generate-reset-token", response_model=PasswordResetTokenResponse)
async def generate_password_reset_token(
    data: PasswordResetTokenGenerate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Generate a password reset token for a user (Admin only).
    
    The admin can generate a token and share it with the user via phone or in-person.
    Token is valid for 1 hour by default.
    """
    # Check if user exists
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate token for inactive user"
        )
    
    # Revoke any existing unused tokens for this user
    existing_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == data.user_id,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).all()
    
    for token in existing_tokens:
        token.is_used = True
        token.used_at = datetime.utcnow()
    
    # Generate new token
    token_string = generate_reset_token()
    expires_at = calculate_token_expiry()
    client_ip = get_client_ip(request)
    
    # Create token record
    reset_token = PasswordResetToken(
        user_id=data.user_id,
        token=token_string,
        token_type="admin_generated",
        expires_at=expires_at,
        generated_by=admin.id,
        ip_address=client_ip
    )
    
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    
    return reset_token


@router.post("/reset-password-with-token")
async def reset_password_with_token(
    data: PasswordResetWithToken,
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset password using a valid token.
    
    This endpoint is public (no authentication required).
    User provides the token given by admin and their new password.
    """
    # Find token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == data.token.upper().strip()
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Check if token is already used
    if reset_token.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used"
        )
    
    # Check if token is expired
    if reset_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has expired. Please request a new one from your administrator"
        )
    
    # Get user
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account not found or inactive"
        )
    
    # Update password with validation and history tracking
    client_ip = get_client_ip(request)
    success, message = update_user_password(
        db=db,
        user=user,
        new_password=data.new_password,
        changed_by=None,
        change_reason="forgot_password",
        ip_address=client_ip
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Mark token as used
    reset_token.is_used = True
    reset_token.used_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Password has been reset successfully. You can now login with your new password."
    }


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change password for authenticated user.
    
    User must provide their current password for verification.
    """
    # Verify current password
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Check if new password is same as current
    if verify_password(data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Update password with validation and history tracking
    client_ip = get_client_ip(request)
    success, message = update_user_password(
        db=db,
        user=current_user,
        new_password=data.new_password,
        changed_by=current_user.id,
        change_reason="user_change",
        ip_address=client_ip
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }


@router.get("/check-password-strength", response_model=PasswordStrengthResponse)
async def check_password_strength(password: str):
    """Check password strength and provide feedback.
    
    This is a utility endpoint to help users create strong passwords.
    """
    is_valid, score, feedback = validate_password_strength(password)
    strength_label = get_password_strength_label(score)
    
    return {
        "strength": strength_label,
        "score": score,
        "feedback": feedback
    }


@router.get("/admin/pending-reset-tokens", response_model=list[dict])
async def get_pending_reset_tokens(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Get all active (unused, non-expired) reset tokens (Admin only).
    
    This helps admins track which tokens are still valid.
    """
    active_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).order_by(PasswordResetToken.created_at.desc()).all()
    
    result = []
    for token in active_tokens:
        user = db.query(User).filter(User.id == token.user_id).first()
        admin_user = db.query(User).filter(User.id == token.generated_by).first() if token.generated_by else None
        
        result.append({
            "id": token.id,
            "token": token.token,
            "user_id": token.user_id,
            "username": user.username if user else "Unknown",
            "full_name": user.full_name if user else "Unknown",
            "expires_at": token.expires_at,
            "created_at": token.created_at,
            "generated_by": admin_user.username if admin_user else "System",
            "minutes_remaining": int((token.expires_at - datetime.utcnow()).total_seconds() / 60)
        })
    
    return result


@router.delete("/admin/revoke-reset-token/{token_id}")
async def revoke_reset_token(
    token_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Revoke (invalidate) a reset token (Admin only).
    
    This allows admins to cancel tokens that were generated by mistake or are no longer needed.
    """
    token = db.query(PasswordResetToken).filter(PasswordResetToken.id == token_id).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    if token.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has already been used and cannot be revoked"
        )
    
    # Mark as used to invalidate it
    token.is_used = True
    token.used_at = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Reset token has been revoked"
    }

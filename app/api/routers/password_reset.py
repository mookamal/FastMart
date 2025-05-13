from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from app.core.config import get_settings
from app.db.base import get_db
from app.services.email.password_reset import PasswordResetService

router = APIRouter()
password_reset_service = PasswordResetService()
settings = get_settings()

@router.post("/auth/forgot-password", response_model=Dict[str, Any])
async def forgot_password(
    email: str = Form(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate the password reset process by sending a reset email.
    """
    # Construct the base URL for the reset link
    base_url = f"{settings.FRONTEND_URL}/reset-password"
    
    # Send password reset email
    await password_reset_service.send_password_reset_email(email, base_url, db)
    
    # Always return success to prevent email enumeration attacks
    return {
        "message": "If your email is registered, you will receive a password reset link"
    }

@router.post("/auth/reset-password", response_model=Dict[str, Any])
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset a user's password using a valid reset token.
    """
    # Verify token and reset password
    success = await password_reset_service.reset_password(token, new_password, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    return {
        "message": "Password has been reset successfully"
    }

@router.get("/auth/verify-reset-token", response_model=Dict[str, Any])
async def verify_reset_token(token: str):
    """
    Verify that a password reset token is valid.
    This endpoint can be used by the frontend to check if a token is valid before showing the reset form.
    """
    payload = await password_reset_service.verify_reset_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    return {
        "valid": True
    }
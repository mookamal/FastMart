from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_token, hash_password
from app.db.models.user import User as UserModel
from app.services.email.service import EmailService
from app.core.config import get_settings

settings = get_settings()

class PasswordResetService:
    """
    Service for handling password reset functionality
    """
    
    def __init__(self):
        self.email_service = EmailService()
        self.token_expire_hours = 24  # Token valid for 24 hours
    
    async def send_password_reset_email(self, email: str, reset_url_base: str, db: AsyncSession) -> bool:
        """
        Generate a password reset token and send a reset email to the user.
        
        Args:
            email: User's email address
            reset_url_base: Base URL for the reset link (e.g., 'https://example.com/reset-password')
            db: Database session
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Find user by email
        stmt = select(UserModel).where(UserModel.email == email)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            # Don't reveal that the user doesn't exist for security reasons
            # Just return True as if we sent the email
            return True
        
        # Generate reset token
        token_data = {
            "sub": str(user.id),
            "type": "password_reset",
            "jti": str(uuid.uuid4())  # Add unique ID to prevent token reuse
        }
        
        expires_delta = timedelta(hours=self.token_expire_hours)
        reset_token = create_access_token(token_data, expires_delta=expires_delta)
        
        # Create reset URL with token
        reset_url = f"{reset_url_base}?token={reset_token}"
        
        # Send email with reset link
        template_body = {
            "reset_url": reset_url,
            "expire_hours": self.token_expire_hours
        }
        
        return await self.email_service.send_email(
            recipients=[email],
            subject="Password Reset Request",
            body="",  # Not used with template
            template_name="password_reset.html",
            template_body=template_body
        )
    
    async def verify_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify that a password reset token is valid.
        
        Args:
            token: The password reset token
            
        Returns:
            Optional[Dict]: The decoded token payload if valid, None otherwise
        """
        try:
            payload = verify_token(token)
            
            # Check if token is a password reset token
            if payload.get("type") != "password_reset":
                return None
                
            return payload
        except ValueError:
            return None
    
    async def reset_password(self, token: str, new_password: str, db: AsyncSession) -> bool:
        """
        Reset a user's password using a valid reset token.
        
        Args:
            token: The password reset token
            new_password: The new password
            db: Database session
            
        Returns:
            bool: True if password was reset successfully, False otherwise
        """
        # Verify token
        payload = await self.verify_reset_token(token)
        if not payload:
            return False
        
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            return False
        
        # Get user to send confirmation email
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if not user:
            return False
        
        # Hash the new password
        hashed_password = hash_password(new_password)
        
        # Update user's password
        update_stmt = update(UserModel).where(UserModel.id == user_id).values(hashed_password=hashed_password)
        await db.execute(update_stmt)
        await db.commit()
        
        # Send confirmation email
        await self.send_password_reset_confirmation(user.email)
        
        return True
        
    async def send_password_reset_confirmation(self, email: str) -> bool:
        """
        Send a confirmation email after a successful password reset.
        
        Args:
            email: User's email address
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        return await self.email_service.send_email(
            recipients=[email],
            subject="Password Reset Successful",
            body="",  # Not used with template
            template_name="password_reset_confirmation.html",
            template_body={}
        )
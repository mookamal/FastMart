from typing import Optional, Dict, Any
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from fastapi import HTTPException, status

from app.db.models.user import User as UserModel
from app.core.security import verify_password, hash_password, create_access_token
from app.core.config import get_settings
from app.services.email.password_reset import PasswordResetService

settings = get_settings()

async def authenticate_user(email: str, password: str, db: AsyncSession) -> Optional[UserModel]:
    """
    Authenticate a user by verifying email and password.
    Returns the user if authentication is successful, None otherwise.
    """
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

async def create_user(email: str, password: str, db: AsyncSession) -> UserModel:
    """
    Create a new user with the given email and password.
    Returns the created user.
    """
    # Check if user already exists
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    hashed_password = hash_password(password)
    user = UserModel(
        id=uuid4(),
        email=email,
        hashed_password=hashed_password
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

async def create_user_token(user: UserModel) -> Dict[str, Any]:
    """
    Create an access token for the given user.
    Returns a dictionary with the token data.
    """
    access_token_expires = timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
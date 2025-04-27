import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from jose import jwt, JWTError

from app.core.config import get_settings

settings = get_settings()

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token encryption configuration
def get_encryption_key() -> bytes:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable is not set")
    # If key is provided as base64, it's ready to use
    # If not, we encode it to bytes and use it as the key
    try:
        return key.encode() if isinstance(key, str) else key
    except Exception as e:
        raise ValueError(f"Invalid encryption key: {str(e)}")

def get_fernet() -> Fernet:
    return Fernet(get_encryption_key())

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def encrypt_token(token: str) -> str:
    """
    Encrypt a token using Fernet symmetric encryption.
    Returns the encrypted token as a base64-encoded string.
    """
    if not token:
        return ""
    
    f = get_fernet()
    encrypted_bytes = f.encrypt(token.encode())
    return encrypted_bytes.decode()

def decrypt_token(encrypted_token: str) -> Optional[str]:
    """
    Decrypt a token using Fernet symmetric encryption.
    Returns the decrypted token as a string, or None if decryption fails.
    """
    if not encrypted_token:
        return None
    
    try:
        f = get_fernet()
        decrypted_bytes = f.decrypt(encrypted_token.encode())
        return decrypted_bytes.decode()
    except InvalidToken:
        return None
    except Exception as e:
        raise ValueError(f"Error decrypting token: {str(e)}")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the given data and expiration time.
    """
    to_encode = data.copy()
    
    # Get expiration time from settings or use default
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    Returns the decoded token payload or raises an exception if invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}") 
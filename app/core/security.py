import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from jose import jwt, JWTError
import hashlib
import hmac
import time
import json
import base64
from urllib.parse import urlencode
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
        # Convert to string if it's not already a string
        if hasattr(encrypted_token, 'decode'):
            # It's bytes
            token_str = encrypted_token.decode()
        elif hasattr(encrypted_token, '__str__'):
            # It's a SQLAlchemy attribute or other object
            token_str = str(encrypted_token)
        else:
            token_str = encrypted_token
            
        # Now encode for decryption
        decrypted_bytes = f.decrypt(token_str.encode())
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

def create_secure_state(user_id: str) -> str:
    """
    Create a secure state parameter with HMAC signature.
    
    Args:
        user_id: The user ID to include in the state
        secret_key: Secret key for HMAC signing
        
    Returns:
        Encoded and signed state string
    """
    secret_key = settings.SECRET_KEY
    # Create state payload
    state_data = {
        "user_id": user_id,
        "timestamp": int(time.time()),
        "nonce": os.urandom(8).hex()  # Add randomness
    }
    
    # Convert to JSON
    state_json = json.dumps(state_data)
    
    # Create HMAC signature
    signature = hmac.new(
        secret_key.encode(),
        state_json.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Combine data and signature
    combined = {
        "data": state_data,
        "signature": signature
    }
    
    # Encode the final state
    return base64.urlsafe_b64encode(json.dumps(combined).encode()).decode()

def verify_secure_state(state: str) -> dict:
    """
    Verify and decode a secure state parameter.
    
    Args:
        state: The state parameter to verify
        secret_key: Secret key for HMAC verification
        
    Returns:
        The verified state data
        
    Raises:
        ValueError: If state is invalid, tampered with, or expired
    """
    secret_key = settings.SECRET_KEY
    try:
        # Decode the state
        decoded = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
        
        # Extract data and signature
        state_data = decoded.get("data")
        received_signature = decoded.get("signature")
        
        if not state_data or not received_signature:
            raise ValueError("Invalid state format")
        
        # Recreate the signature for verification
        expected_signature = hmac.new(
            secret_key.encode(),
            json.dumps(state_data).encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature
        if not hmac.compare_digest(expected_signature, received_signature):
            raise ValueError("State signature verification failed")
        
        # Verify timestamp (e.g., 15 minutes expiry)
        current_time = int(time.time())
        if current_time - state_data.get("timestamp", 0) > 900:  # 15 minutes
            raise ValueError("State has expired")
            
        return state_data
        
    except Exception as e:
        raise ValueError(f"Invalid state parameter: {str(e)}")
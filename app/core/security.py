import os
from typing import Optional
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

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
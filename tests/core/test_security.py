import os
import pytest
from cryptography.fernet import Fernet
from app.core.security import (
    hash_password,
    verify_password,
    encrypt_token,
    decrypt_token,
    get_encryption_key
)

# Test data
TEST_PASSWORD = "mysecretpassword123"
TEST_TOKEN = "shpat_12345abcde67890fghijk"
TEST_ENCRYPTION_KEY = Fernet.generate_key()

@pytest.fixture(autouse=True)
def setup_encryption_key(monkeypatch):
    """Setup test encryption key for all tests"""
    monkeypatch.setenv("ENCRYPTION_KEY", TEST_ENCRYPTION_KEY.decode())

def test_password_hashing():
    """Test that password hashing and verification work correctly"""
    # Hash the password
    hashed = hash_password(TEST_PASSWORD)
    
    # Verify the hash is different from the original password
    assert hashed != TEST_PASSWORD
    
    # Verify the password matches its hash
    assert verify_password(TEST_PASSWORD, hashed) is True
    
    # Verify incorrect password fails
    assert verify_password("wrongpassword", hashed) is False

def test_token_encryption():
    """Test that token encryption and decryption work correctly"""
    # Encrypt the token
    encrypted = encrypt_token(TEST_TOKEN)
    
    # Verify the encrypted token is different from the original
    assert encrypted != TEST_TOKEN
    
    # Decrypt and verify it matches the original
    decrypted = decrypt_token(encrypted)
    assert decrypted == TEST_TOKEN

def test_token_encryption_empty_values():
    """Test handling of empty/None values in token encryption"""
    # Test empty string
    assert encrypt_token("") == ""
    assert decrypt_token("") is None
    
    # Test None value for encryption
    assert encrypt_token(None) == ""

def test_token_decryption_invalid_token():
    """Test decryption with invalid token"""
    # Test with invalid encrypted data
    assert decrypt_token("invalid_token") is None
    
    # Test with valid base64 but invalid token
    invalid_token = "d2VsbCB0aGlzIGlzIG5vdCBhIHZhbGlkIHRva2Vu"  # base64 encoded
    assert decrypt_token(invalid_token) is None

def test_encryption_key_environment():
    """Test encryption key retrieval"""
    key = get_encryption_key()
    assert isinstance(key, bytes)
    assert len(key) > 0

def test_token_encryption_consistency():
    """Test that encryption/decryption is consistent across multiple operations"""
    # Encrypt the same token multiple times
    encrypted1 = encrypt_token(TEST_TOKEN)
    encrypted2 = encrypt_token(TEST_TOKEN)
    
    # Each encryption should produce different results (due to random IV)
    assert encrypted1 != encrypted2
    
    # But both should decrypt to the same original token
    assert decrypt_token(encrypted1) == TEST_TOKEN
    assert decrypt_token(encrypted2) == TEST_TOKEN 
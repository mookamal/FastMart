from pydantic import BaseModel
from typing import List, Optional
from functools import lru_cache
import os
from app.core.config import get_settings

class EmailSettings(BaseModel):
    """Email configuration settings"""
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "noreply@example.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", get_settings().PROJECT_NAME)
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS", "True").lower() in ("true", "1", "t")
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "False").lower() in ("true", "1", "t")
    MAIL_USE_CREDENTIALS: bool = os.getenv("MAIL_USE_CREDENTIALS", "True").lower() in ("true", "1", "t")
    MAIL_VALIDATE_CERTS: bool = os.getenv("MAIL_VALIDATE_CERTS", "True").lower() in ("true", "1", "t")
    MAIL_SUPPRESS_SEND: bool = os.getenv("MAIL_SUPPRESS_SEND", "False").lower() in ("true", "1", "t")
    CONTACT_RECIPIENTS: List[str] = os.getenv("CONTACT_RECIPIENTS", "admin@example.com").split(",")

@lru_cache()
def get_email_settings() -> EmailSettings:
    """Returns cached email settings"""
    return EmailSettings()
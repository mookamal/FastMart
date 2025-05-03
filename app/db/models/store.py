import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.db.base import Base
from app.core.security import encrypt_token, decrypt_token

class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False, default="shopify", index=True)
    currency = Column(String(3), default='USD', nullable=False)
    shop_domain = Column(String(255), nullable=False)
    _access_token = Column('access_token', Text, nullable=False)
    scope = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="stores")
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="store", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")

    __table_args__ = (
        # Unique constraint for user_id, shop_domain, and platform
    )

    @hybrid_property
    def access_token(self) -> str:
        """
        Decrypt and return the access token.
        Returns empty string if decryption fails.
        """
        decrypted = decrypt_token(self._access_token)
        return decrypted if decrypted is not None else ""

    @access_token.setter
    def access_token(self, token: str) -> None:
        """
        Encrypt and store the access token.
        """
        if token is None:
            self._access_token = ""
        else:
            self._access_token = encrypt_token(token)
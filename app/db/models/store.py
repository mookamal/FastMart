import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String(50), nullable=False, default="shopify", index=True)
    shop_domain = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False)
    scope = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="stores")

    __table_args__ = (
        # Unique constraint for user_id, shop_domain, and platform
        {"sqlite_autoincrement": True},
    ) 
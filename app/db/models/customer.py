from sqlalchemy import (Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    platform_customer_id = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    orders_count = Column(Integer, default=0, nullable=False)
    total_spent = Column(Numeric(12, 2), default=0.00, nullable=False)
    platform_created_at = Column(TIMESTAMP(timezone=True), nullable=True)
    platform_updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    synced_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    store = relationship("Store", back_populates="customers")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('store_id', 'platform_customer_id', name='uq_store_platform_customer'),)
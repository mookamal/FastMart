from sqlalchemy import (Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = 'orders'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=True)
    platform_order_id = Column(String(100), nullable=False)
    order_number = Column(String(100), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    financial_status = Column(String(50), nullable=True)
    fulfillment_status = Column(String(50), nullable=True)
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    platform_created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    platform_updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    synced_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    store = relationship("Store", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    line_items = relationship("LineItem", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('store_id', 'platform_order_id', name='uq_store_platform_order'),)
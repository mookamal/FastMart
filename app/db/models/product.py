from sqlalchemy import (Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Product(Base):
    __tablename__ = 'products'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    platform_product_id = Column(String(100), nullable=False)
    title = Column(Text, nullable=False)
    vendor = Column(String(255), nullable=True)
    product_type = Column(String(255), nullable=True)
    platform_created_at = Column(TIMESTAMP(timezone=True), nullable=True)
    platform_updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    synced_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    inventory_levels = Column(JSONB, nullable=True)

    store = relationship("Store", back_populates="products")
    line_items = relationship("LineItem", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('store_id', 'platform_product_id', name='uq_store_platform_product'),)
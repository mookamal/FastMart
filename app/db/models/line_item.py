from sqlalchemy import (Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Boolean, func)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class LineItem(Base):
    __tablename__ = 'line_items'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=True)
    platform_line_item_id = Column(String(100), nullable=False)
    platform_product_id = Column(String(100), nullable=True)
    platform_variant_id = Column(String(100), nullable=True)
    title = Column(Text, nullable=False)
    variant_title = Column(Text, nullable=True)
    sku = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    # Additional fields for analytics
    total_discount = Column(Numeric(12, 2), nullable=True)
    tax_lines = Column(JSONB, nullable=True)
    properties = Column(JSONB, nullable=True)
    fulfillment_status = Column(String(50), nullable=True)
    requires_shipping = Column(Boolean, default=True, nullable=False)
    gift_card = Column(Boolean, default=False, nullable=False)
    taxable = Column(Boolean, default=True, nullable=False)

    order = relationship("Order", back_populates="line_items")
    product = relationship("Product", back_populates="line_items")

    __table_args__ = (UniqueConstraint('order_id', 'platform_line_item_id', name='uq_order_platform_line_item'),)
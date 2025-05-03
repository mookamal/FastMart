from sqlalchemy import (Column,  ForeignKey, Integer, Numeric, String,Boolean, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base

class ProductVariant(Base):
    __tablename__ = 'product_variants'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    platform_variant_id = Column(String(100), nullable=False)
    title = Column(String(255), nullable=True)
    sku = Column(String(100), nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    compare_at_price = Column(Numeric(10, 2), nullable=True)
    position = Column(Integer, nullable=True)
    inventory_item_id = Column(String(100), nullable=True)
    inventory_quantity = Column(Integer, nullable=True, default=0)
    weight = Column(Numeric(10, 2), nullable=True)
    weight_unit = Column(String(20), nullable=True)
    option1 = Column(String(255), nullable=True)
    option2 = Column(String(255), nullable=True)
    option3 = Column(String(255), nullable=True)
    taxable = Column(Boolean, nullable=True, default=True)
    barcode = Column(String(100), nullable=True)
    image_id = Column(String(100), nullable=True)
    platform_created_at = Column(TIMESTAMP(timezone=True), nullable=True)
    platform_updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    synced_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product", back_populates="variants")

    __table_args__ = (UniqueConstraint('product_id', 'platform_variant_id', name='uq_product_platform_variant'),)
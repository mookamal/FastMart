from sqlalchemy import Column, ForeignKey, String, Numeric, Boolean, Integer, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base

class ShippingCostRule(Base):
    __tablename__ = 'shipping_cost_rules'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # Higher priority rules are evaluated first
    
    # Rule conditions (e.g., country, weight range, price range)
    conditions = Column(JSONB, nullable=False)
    
    # Cost calculation (fixed amount, percentage, or formula)
    cost_type = Column(String(50), nullable=False)  # 'fixed', 'percentage', 'formula'
    cost_value = Column(Numeric(12, 2), nullable=False)  # Fixed amount or percentage value
    cost_formula = Column(String(500), nullable=True)  # Optional formula for complex calculations
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    store = relationship("Store", back_populates="shipping_cost_rules")
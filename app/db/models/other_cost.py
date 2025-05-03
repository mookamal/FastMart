from sqlalchemy import Column, ForeignKey, String, Date, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base

class OtherCost(Base):
    __tablename__ = 'other_costs'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    category = Column(String(100), nullable=False)  # e.g., 'subscription', 'rent', 'salary', etc.
    description = Column(Text, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Null for ongoing costs
    frequency = Column(String(50), nullable=False)  # e.g., 'monthly', 'one-time', 'yearly', etc.
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    store = relationship("Store", back_populates="other_costs")
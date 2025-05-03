from sqlalchemy import Column, ForeignKey, String, Date, Numeric, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base import Base

class AdSpend(Base):
    __tablename__ = 'ad_spends'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    platform = Column(String(100), nullable=False)  # e.g., 'facebook', 'google', etc.
    date = Column(Date, nullable=False)
    spend = Column(Numeric(12, 2), nullable=False)
    campaign_name = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    store = relationship("Store", back_populates="ad_spends")
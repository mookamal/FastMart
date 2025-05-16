from sqlalchemy import Column, Date, Numeric, ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.db.base import Base
from sqlalchemy.orm import relationship
class DailySalesAnalytics(Base):
    """Model for storing precomputed daily sales analytics."""
    __tablename__ = "daily_sales_analytics"
    
    id = Column(UUID(as_uuid=True), default=uuid4, nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_sales = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    total_orders = Column(Numeric(precision=10, scale=0), nullable=False, default=0)
    average_order_value = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    profit = Column(Numeric(precision=10, scale=2), nullable=False, default=0)

    store = relationship("Store", back_populates="daily_sales_analytics")
    # Add composite index for faster querying by store and date range
    __table_args__ = (
        PrimaryKeyConstraint('id', 'date'),
        Index('idx_store_date', 'store_id', 'date'),
        {'postgresql_partition_by': 'RANGE (date)'}
    )

    
    def __repr__(self):
        return f"<DailySalesAnalytics(store_id={self.store_id}, date={self.date}>"
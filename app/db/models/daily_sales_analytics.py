from sqlalchemy import Column, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.db.base import Base

class DailySalesAnalytics(Base):
    """Model for storing precomputed daily sales analytics."""
    __tablename__ = "daily_sales_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("store.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_sales = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    total_orders = Column(Numeric(precision=10, scale=0), nullable=False, default=0)
    average_order_value = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    profit = Column(Numeric(precision=10, scale=2), nullable=False, default=0)
    
    # Add composite index for faster querying by store and date range
    __table_args__ = (
        # Create a composite index on store_id and date for faster lookups
        {'postgresql_partition_by': 'RANGE (date)'}
    )
    
    def __repr__(self):
        return f"<DailySalesAnalytics(store_id={self.store_id}, date={self.date}>"
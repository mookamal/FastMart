from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Union
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.daily_sales_analytics import DailySalesAnalytics
from app.db.models.order import Order
from app.services.analytics.profit_calculator import ProfitCalculator


class DailySalesAnalyticsService:
    """Service for calculating and managing daily sales analytics data."""
    
    @staticmethod
    async def get_daily_analytics(
        db: AsyncSession,
        store_id: Union[str, UUID],
        start_date: date,
        end_date: date
    ) -> List[DailySalesAnalytics]:
        """Retrieve daily sales analytics for a date range.
        
        Args:
            db: Database session
            store_id: Store ID (string or UUID)
            start_date: Start date for the query
            end_date: End date for the query
            
        Returns:
            List of DailySalesAnalytics objects
        """
        # Convert string ID to UUID if needed
        store_uuid = store_id if isinstance(store_id, UUID) else UUID(store_id)
        
        # Query for existing analytics records
        query = select(DailySalesAnalytics).where(
            and_(
                DailySalesAnalytics.store_id == store_uuid,
                DailySalesAnalytics.date >= start_date,
                DailySalesAnalytics.date <= end_date
            )
        ).order_by(DailySalesAnalytics.date)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def calculate_and_store_daily_analytics(
        db: AsyncSession,
        store_id: Union[str, UUID],
        target_date: date
    ) -> DailySalesAnalytics:
        """Calculate and store daily sales analytics for a specific date.
        
        Args:
            db: Database session
            store_id: Store ID (string or UUID)
            target_date: The date to calculate analytics for
            
        Returns:
            Created or updated DailySalesAnalytics object
        """
        # Convert string ID to UUID if needed
        store_uuid = store_id if isinstance(store_id, UUID) else UUID(store_id)
        
        # Convert date to datetime range for the full day
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # Check if analytics already exist for this date
        query = select(DailySalesAnalytics).where(
            and_(
                DailySalesAnalytics.store_id == store_uuid,
                DailySalesAnalytics.date == target_date
            )
        )
        result = await db.execute(query)
        existing_analytics = result.scalar_one_or_none()
        
        # Calculate order metrics for the day
        orders_query = select(Order).where(
            and_(
                Order.store_id == store_uuid,
                Order.created_at >= start_datetime,
                Order.created_at <= end_datetime,
                Order.status != 'cancelled'
            )
        )
        orders_result = await db.execute(orders_query)
        orders = orders_result.scalars().all()
        
        # Calculate total sales and order count
        total_sales = sum(order.total_price for order in orders)
        total_orders = len(orders)
        average_order_value = Decimal('0')
        if total_orders > 0:
            average_order_value = Decimal(total_sales) / Decimal(total_orders)
        
        # Calculate profit using the ProfitCalculator
        profit_data = await ProfitCalculator.calculate_net_profit(
            db=db,
            store_id=str(store_uuid),
            start_date=start_datetime,
            end_date=end_datetime
        )
        profit = profit_data["net_profit"]
        
        if existing_analytics:
            # Update existing record
            existing_analytics.total_sales = total_sales
            existing_analytics.total_orders = total_orders
            existing_analytics.average_order_value = average_order_value
            existing_analytics.profit = profit
            await db.commit()
            return existing_analytics
        else:
            # Create new record
            new_analytics = DailySalesAnalytics(
                store_id=store_uuid,
                date=target_date,
                total_sales=total_sales,
                total_orders=total_orders,
                average_order_value=average_order_value,
                profit=profit
            )
            db.add(new_analytics)
            await db.commit()
            return new_analytics
    
    @staticmethod
    async def update_analytics_for_date_range(
        db: AsyncSession,
        store_id: Union[str, UUID],
        start_date: date,
        end_date: date
    ) -> List[DailySalesAnalytics]:
        """Calculate and store analytics for each day in a date range.
        
        Args:
            db: Database session
            store_id: Store ID (string or UUID)
            start_date: Start date for the calculation
            end_date: End date for the calculation
            
        Returns:
            List of created or updated DailySalesAnalytics objects
        """
        # Convert string ID to UUID if needed
        store_uuid = store_id if isinstance(store_id, UUID) else UUID(store_id)
        
        results = []
        current_date = start_date
        
        # Process each day in the range
        while current_date <= end_date:
            analytics = await DailySalesAnalyticsService.calculate_and_store_daily_analytics(
                db=db,
                store_id=store_uuid,
                target_date=current_date
            )
            results.append(analytics)
            current_date += timedelta(days=1)
        
        return results
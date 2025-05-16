from decimal import Decimal
from typing import List
from strawberry.types import Info

from app.api.graphql.common.inputs import DateRangeInput
from app.api.graphql.analytics.daily_sales_types import DailySalesAnalytics, DailySalesAnalyticsSummary
from app.services.analytics.daily_sales_service import DailySalesAnalyticsService

async def resolve_daily_sales_analytics(
    info: Info, 
    store_id: str, 
    date_range: DateRangeInput
) -> List[DailySalesAnalytics]:
    """Resolver for fetching daily sales analytics for a date range.
    
    Args:
        info: GraphQL resolver info
        store_id: Store ID
        date_range: Date range for the query
        
    Returns:
        List of DailySalesAnalytics objects
    """
    context = info.context
    db = context["db"]
    
    # Fetch analytics from the database
    analytics_records = await DailySalesAnalyticsService.get_daily_analytics(
        db=db,
        store_id=store_id,
        start_date=date_range.start_date,
        end_date=date_range.end_date
    )
    
    # Convert database models to GraphQL types
    return [
        DailySalesAnalytics(
            id=str(record.id),
            store_id=str(record.store_id),
            date=record.date,
            total_sales=record.total_sales,
            total_orders=int(record.total_orders),
            average_order_value=record.average_order_value,
            profit=record.profit
        ) for record in analytics_records
    ]

async def resolve_daily_sales_analytics_summary(
    info: Info, 
    store_id: str, 
    date_range: DateRangeInput
) -> DailySalesAnalyticsSummary:
    """Resolver for fetching a summary of daily sales analytics for a date range.
    
    Args:
        info: GraphQL resolver info
        store_id: Store ID
        date_range: Date range for the query
        
    Returns:
        DailySalesAnalyticsSummary object
    """
    context = info.context
    db = context["db"]
    
    # Fetch analytics from the database
    analytics_records = await DailySalesAnalyticsService.get_daily_analytics(
        db=db,
        store_id=store_id,
        start_date=date_range.start_date,
        end_date=date_range.end_date
    )
    
    # Convert database models to GraphQL types
    daily_analytics = [
        DailySalesAnalytics(
            id=str(record.id),
            store_id=str(record.store_id),
            date=record.date,
            total_sales=record.total_sales,
            total_orders=int(record.total_orders),
            average_order_value=record.average_order_value,
            profit=record.profit
        ) for record in analytics_records
    ]
    
    # Calculate summary metrics
    total_sales = sum(record.total_sales for record in analytics_records)
    total_orders = sum(int(record.total_orders) for record in analytics_records)
    total_profit = sum(record.profit for record in analytics_records)
    
    # Calculate average order value across the entire period
    average_order_value = Decimal('0')
    if total_orders > 0:
        average_order_value = total_sales / Decimal(total_orders)
    
    return DailySalesAnalyticsSummary(
        start_date=date_range.start_date,
        end_date=date_range.end_date,
        total_sales=total_sales,
        total_orders=total_orders,
        average_order_value=average_order_value,
        total_profit=total_profit,
        daily_analytics=daily_analytics
    )
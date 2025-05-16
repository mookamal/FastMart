import strawberry
from typing import List, Optional
from strawberry.scalars import ID
from app.api.graphql.types.scalars import Numeric, Date

@strawberry.type
class DailySalesAnalytics:
    """GraphQL type for daily sales analytics data."""
    id: ID
    store_id: ID
    date: Date
    total_sales: Numeric
    total_orders: int
    average_order_value: Numeric
    profit: Numeric

@strawberry.type
class DailySalesAnalyticsSummary:
    """Summary of daily sales analytics over a period."""
    start_date: Date
    end_date: Date
    total_sales: Numeric
    total_orders: int
    average_order_value: Numeric
    total_profit: Numeric
    daily_analytics: List[DailySalesAnalytics]
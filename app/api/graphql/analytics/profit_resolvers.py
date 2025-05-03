from typing import Optional
from uuid import UUID
from datetime import datetime
from strawberry.types import Info

from app.api.graphql.analytics.profit_types import ProfitMetrics
from app.services.analytics.profit_calculator import ProfitCalculator
from app.api.graphql.common.inputs import DateRangeInput

async def resolve_profit_metrics(info: Info, store_id: str, date_range: DateRangeInput) -> ProfitMetrics:
    """Resolver for profit metrics calculation.
    
    Args:
        info: GraphQL resolver info
        store_id: Store ID
        date_range: Date range for the calculation
        
    Returns:
        ProfitMetrics object containing all profit-related metrics
    """
    context = info.context
    db = context["db"]
    
    # Convert date strings to datetime objects with timezone info for proper comparison
    start_date = datetime.combine(date_range.start_date, datetime.min.time())
    end_date = datetime.combine(date_range.end_date, datetime.max.time())
    
    # Calculate profit metrics
    profit_data = await ProfitCalculator.calculate_net_profit(
        db=db,
        store_id=store_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Create and return ProfitMetrics object
    return ProfitMetrics(
        gross_revenue=profit_data["gross_revenue"],
        net_revenue=profit_data["net_revenue"],
        gross_profit=profit_data["gross_profit"],
        net_profit=profit_data["net_profit"],
        total_cogs=profit_data["total_cogs"],
        total_shipping_cost=profit_data["total_shipping_cost"],
        total_transaction_fees=profit_data["total_transaction_fees"],
        total_ad_spend=profit_data["total_ad_spend"],
        total_other_costs=profit_data["total_other_costs"],
        total_refunds=profit_data["total_refunds"],
        total_discounts=profit_data["total_discounts"]
    )
import strawberry
from typing import Optional
from app.api.graphql.types.scalars import Numeric
from app.api.graphql.common.inputs import DateRangeInput

@strawberry.type
class ProfitMetrics:
    """Type representing profit metrics for a store."""
    gross_revenue: Numeric
    net_revenue: Numeric
    gross_profit: Numeric
    net_profit: Numeric
    total_cogs: Numeric
    total_shipping_cost: Numeric
    total_transaction_fees: Numeric
    total_ad_spend: Numeric
    total_other_costs: Numeric
    total_refunds: Numeric
    total_discounts: Numeric
    
    @strawberry.field
    def profit_margin(self) -> Numeric:
        """Calculate profit margin as a percentage of net revenue."""
        if self.net_revenue == 0:
            return 0
        return (self.net_profit / self.net_revenue) * 100
    
    @strawberry.field
    def gross_margin(self) -> Numeric:
        """Calculate gross margin as a percentage of net revenue."""
        if self.net_revenue == 0:
            return 0
        return (self.gross_profit / self.net_revenue) * 100
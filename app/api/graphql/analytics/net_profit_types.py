import strawberry
from typing import List, Optional
from strawberry.scalars import ID
from app.api.graphql.types.scalars import Numeric, Date
from app.api.graphql.common.inputs import DateRangeInput
from app.api.graphql.analytics.types import AdSpend, OtherCost

@strawberry.type
class NetProfitMetrics:
    """Type representing net profit metrics for a store."""
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

@strawberry.type
class PnlReportItem:
    """Type representing a line item in a P&L report."""
    category: str
    amount: Numeric
    percentage: Numeric

@strawberry.type
class PnlReport:
    """Type representing a structured P&L report."""
    revenue: PnlReportItem
    cogs: PnlReportItem
    gross_profit: PnlReportItem
    expenses: List[PnlReportItem]
    net_profit: PnlReportItem

@strawberry.type
class CustomerLtvMetrics:
    """Type representing customer lifetime value metrics."""
    customer_id: ID
    total_orders: int
    total_revenue: Numeric
    total_profit: Numeric
    net_profit_ltv: Numeric
    average_order_value: Numeric
    average_profit_per_order: Numeric
    first_order_date: Date
    last_order_date: Date
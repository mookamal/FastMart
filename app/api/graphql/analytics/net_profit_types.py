import strawberry
from typing import List
from app.api.graphql.types.scalars import Numeric

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
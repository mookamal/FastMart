from typing import List, Optional
from uuid import UUID
from datetime import datetime
from strawberry.types import Info

from app.api.graphql.analytics.net_profit_types import NetProfitMetrics, PnlReport, PnlReportItem
from app.services.analytics.profit_calculator import ProfitCalculator
from app.api.graphql.common.inputs import DateRangeInput
from app.db.models.ad_spend import AdSpend
from app.db.models.other_cost import OtherCost
from sqlalchemy import select, and_
from app.api.graphql.analytics.types import AdSpend as AdSpendType, OtherCost as OtherCostType

async def resolve_net_profit_analytics(info: Info, store_id: str, date_range: DateRangeInput) -> NetProfitMetrics:
    """Resolver for net profit analytics calculation.
    
    Args:
        info: GraphQL resolver info
        store_id: Store ID
        date_range: Date range for the calculation
        
    Returns:
        NetProfitMetrics object containing all net profit-related metrics
    """
    context = info.context
    db = context["db"]
    
    # Convert date strings to datetime objects with timezone info for proper comparison
    start_date = datetime.combine(date_range.start_date, datetime.min.time())
    end_date = datetime.combine(date_range.end_date, datetime.max.time())
    
    # Calculate profit metrics using the existing ProfitCalculator
    profit_data = await ProfitCalculator.calculate_net_profit(
        db=db,
        store_id=store_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Create and return NetProfitMetrics object
    return NetProfitMetrics(
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

async def resolve_profit_and_loss_report(info: Info, store_id: str, date_range: DateRangeInput) -> PnlReport:
    """Resolver for profit and loss report.
    
    Args:
        info: GraphQL resolver info
        store_id: Store ID
        date_range: Date range for the calculation
        
    Returns:
        PnlReport object containing structured P&L data
    """
    context = info.context
    db = context["db"]
    
    # Convert date strings to datetime objects
    start_date = datetime.combine(date_range.start_date, datetime.min.time())
    end_date = datetime.combine(date_range.end_date, datetime.max.time())
    
    # Calculate profit metrics
    profit_data = await ProfitCalculator.calculate_net_profit(
        db=db,
        store_id=store_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Calculate percentages based on net revenue
    net_revenue = profit_data["net_revenue"]
    percentage_base = net_revenue if net_revenue > 0 else 1  # Avoid division by zero
    
    # Create report items
    revenue_item = PnlReportItem(
        category="Revenue",
        amount=net_revenue,
        percentage=100.0  # Revenue is always 100% of itself
    )
    
    cogs_item = PnlReportItem(
        category="Cost of Goods Sold",
        amount=profit_data["total_cogs"],
        percentage=(profit_data["total_cogs"] / percentage_base) * 100
    )
    
    gross_profit_item = PnlReportItem(
        category="Gross Profit",
        amount=profit_data["gross_profit"],
        percentage=(profit_data["gross_profit"] / percentage_base) * 100
    )
    
    # Create expense items
    expenses = [
        PnlReportItem(
            category="Shipping Costs",
            amount=profit_data["total_shipping_cost"],
            percentage=(profit_data["total_shipping_cost"] / percentage_base) * 100
        ),
        PnlReportItem(
            category="Transaction Fees",
            amount=profit_data["total_transaction_fees"],
            percentage=(profit_data["total_transaction_fees"] / percentage_base) * 100
        ),
        PnlReportItem(
            category="Advertising",
            amount=profit_data["total_ad_spend"],
            percentage=(profit_data["total_ad_spend"] / percentage_base) * 100
        ),
        PnlReportItem(
            category="Other Costs",
            amount=profit_data["total_other_costs"],
            percentage=(profit_data["total_other_costs"] / percentage_base) * 100
        )
    ]
    
    net_profit_item = PnlReportItem(
        category="Net Profit",
        amount=profit_data["net_profit"],
        percentage=(profit_data["net_profit"] / percentage_base) * 100
    )
    
    # Create and return PnlReport
    return PnlReport(
        revenue=revenue_item,
        cogs=cogs_item,
        gross_profit=gross_profit_item,
        expenses=expenses,
        net_profit=net_profit_item
    )



async def resolve_ad_spend_entries(info: Info, store_id: str, date_range: Optional[DateRangeInput] = None) -> List[AdSpendType]:
    """Resolver to retrieve ad spend entries."""
    context = info.context
    db = context["db"]
    store_uuid = UUID(store_id)
    
    query = select(AdSpend).where(AdSpend.store_id == store_uuid)
    
    if date_range:
        start_date = date_range.start_date
        end_date = date_range.end_date
        query = query.where(
            and_(
                AdSpend.date >= start_date,
                AdSpend.date <= end_date
            )
        )
    
    result = await db.execute(query)
    ad_spends = result.scalars().all()
    
    return [
        AdSpendType(
            id=str(ad_spend.id),
            platform=ad_spend.platform,
            date=ad_spend.date,
            spend=ad_spend.spend,
            campaign_name=ad_spend.campaign_name
        ) for ad_spend in ad_spends
    ]

async def resolve_other_cost_entries(info: Info, store_id: str) -> List[OtherCostType]:
    """Resolver to retrieve other cost entries."""
    context = info.context
    db = context["db"]
    store_uuid = UUID(store_id)
    
    query = select(OtherCost).where(OtherCost.store_id == store_uuid)
    
    result = await db.execute(query)
    other_costs = result.scalars().all()
    
    return [
        OtherCostType(
            id=str(other_cost.id),
            category=other_cost.category,
            description=other_cost.description,
            amount=other_cost.amount,
            start_date=other_cost.start_date,
            end_date=other_cost.end_date,
            frequency=other_cost.frequency
        ) for other_cost in other_costs
    ]
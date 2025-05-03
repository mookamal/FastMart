import strawberry
from typing import List, Optional
from strawberry.scalars import ID
from app.api.graphql.types.scalars import Numeric, Date, DateTime
from app.api.graphql.products.types import Product
from app.api.graphql.common.inputs import DateRangeInput

@strawberry.type
class AnalyticsSummary:
    total_sales: Numeric
    order_count: int
    average_order_value: Numeric
    new_customer_count: int

@strawberry.type
class ProductAnalytics:
    product: "Product"
    total_quantity_sold: int
    total_revenue: Numeric

@strawberry.type
class TimeSeriesDataPoint:
    date: Date
    value: Numeric

@strawberry.type
class ProductVariantAnalytics:
    product_id: ID
    title: str
    variant_title: Optional[str] = None
    sku: Optional[str] = None
    
    @strawberry.field
    async def total_units_sold(self, info, date_range: Optional[DateRangeInput] = None) -> int:
        from app.api.graphql.analytics.resolvers import resolve_product_total_units_sold
        return await resolve_product_total_units_sold(self.product_id, date_range, info)
    
    @strawberry.field
    async def total_revenue(self, info, date_range: Optional[DateRangeInput] = None) -> Numeric:
        from app.api.graphql.analytics.resolvers import resolve_product_total_revenue
        return await resolve_product_total_revenue(self.product_id, date_range, info)
    
    @strawberry.field
    async def average_selling_price(self, info, date_range: Optional[DateRangeInput] = None) -> Numeric:
        from app.api.graphql.analytics.resolvers import resolve_product_average_selling_price
        return await resolve_product_average_selling_price(self.product_id, date_range, info)
    
    @strawberry.field
    async def inventory_level(self, info) -> Optional[int]:
        from app.api.graphql.analytics.resolvers import resolve_product_inventory_level
        return await resolve_product_inventory_level(self.product_id, info)

@strawberry.type
class DiscountCodeAnalytics:
    code: str
    usage_count: int
    total_discount_amount: Numeric
    total_sales_generated: Numeric

# Input Types for Cost Management
@strawberry.input
class ProductVariantCogsInput:
    """Input type for updating cost of goods sold for a product variant."""
    variant_id: strawberry.ID
    cogs: Numeric

@strawberry.input
class AdSpendInput:
    """Input type for adding ad spend records."""
    store_id: strawberry.ID
    platform: str
    date: Date
    spend: Numeric
    campaign_name: Optional[str] = None

@strawberry.input
class OtherCostInput:
    """Input type for adding other cost records."""
    store_id: strawberry.ID
    category: str
    description: str
    amount: Numeric
    start_date: Date
    end_date: Optional[Date] = None
    frequency: str = "one_time"  # one_time, monthly, quarterly, yearly

@strawberry.input
class ShippingCostRuleInput:
    """Input type for shipping cost rules."""
    store_id: strawberry.ID
    name: str
    base_cost: Numeric
    per_item_cost: Numeric = 0
    is_default: bool = False

@strawberry.input
class TransactionFeeRuleInput:
    """Input type for transaction fee rules."""
    store_id: strawberry.ID
    platform: str
    percentage: Numeric
    fixed_fee: Numeric = 0

# Object Types for Cost Management
@strawberry.type
class ProductVariant:
    """GraphQL type for product variant."""
    id: strawberry.ID
    title: str
    sku: Optional[str] = None
    cost_of_goods_sold: Optional[Numeric] = None

@strawberry.type
class AdSpend:
    """GraphQL type for ad spend."""
    id: strawberry.ID
    platform: str
    date: Date
    spend: Numeric
    campaign_name: Optional[str] = None

@strawberry.type
class OtherCost:
    """GraphQL type for other costs."""
    id: strawberry.ID
    category: str
    description: str
    amount: Numeric
    start_date: Date
    end_date: Optional[Date] = None
    frequency: str

@strawberry.type
class ShippingCostRule:
    """GraphQL type for shipping cost rules."""
    id: strawberry.ID
    name: str
    base_cost: Numeric
    per_item_cost: Numeric
    is_default: bool

@strawberry.type
class TransactionFeeRule:
    """GraphQL type for transaction fee rules."""
    id: strawberry.ID
    platform: str
    percentage: Numeric
    fixed_fee: Numeric
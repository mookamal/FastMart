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
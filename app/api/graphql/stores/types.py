from typing import List, Optional
import strawberry
from strawberry.scalars import ID
from app.api.graphql.types.scalars import DateTime
from app.api.graphql.common.enums import TimeInterval
from app.api.graphql.products.types import Product
from app.api.graphql.customers.types import Customer
from app.api.graphql.orders.types import Order
from app.api.graphql.analytics.types import AnalyticsSummary, ProductAnalytics, TimeSeriesDataPoint
from app.api.graphql.common.inputs import DateRangeInput


@strawberry.type
class Store:
    id: ID
    platform: str
    shop_domain: str
    is_active: bool
    last_sync_at: Optional[DateTime] = None
    currency: str
    created_at: DateTime
    
    @strawberry.field
    async def products(self, info) -> List["Product"]:
        from app.api.graphql.stores.resolvers import resolve_store_products
        return await resolve_store_products(self, info)
    
    @strawberry.field
    async def customers(self, info) -> List["Customer"]:
        from app.api.graphql.stores.resolvers import resolve_store_customers
        return await resolve_store_customers(self, info)
    
    @strawberry.field
    async def orders(self, info) -> List["Order"]:
        from app.api.graphql.stores.resolvers import resolve_store_orders
        return await resolve_store_orders(self, info)
        
    @strawberry.field
    async def analytics_summary(self, info, date_range: "DateRangeInput") -> AnalyticsSummary:
        from app.api.graphql.analytics.resolvers import resolve_analytics_summary
        return await resolve_analytics_summary(self.id, date_range, info)
    
    @strawberry.field
    async def top_selling_products(self, info, date_range: "DateRangeInput", limit: int = 5) -> List["ProductAnalytics"]:
        from app.api.graphql.analytics.resolvers import resolve_top_selling_products
        return await resolve_top_selling_products(self.id, date_range, limit, info)
    
    @strawberry.field
    async def orders_over_time(self, info, date_range: "DateRangeInput", interval: TimeInterval = TimeInterval.DAY) -> List["TimeSeriesDataPoint"]:
        from app.api.graphql.analytics.resolvers import resolve_orders_over_time
        return await resolve_orders_over_time(self.id, date_range, interval, info)
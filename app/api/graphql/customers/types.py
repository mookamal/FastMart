from typing import Optional, List
import strawberry
from strawberry.scalars import ID
from app.api.graphql.types.scalars import DateTime, Numeric,Date
from uuid import UUID

@strawberry.type
class Customer:
    id: ID
    platform_customer_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    platform_created_at: Optional[DateTime] = None
    platform_updated_at: Optional[DateTime] = None
    synced_at: DateTime
    # Hidden field (not in GraphQL schema)
    store_id: strawberry.Private[ID]
    @strawberry.field
    async def ltv_metrics(self, info) -> "CustomerLtvMetrics":
        from app.api.graphql.customers.resolvers import CustomerResolver
        return await CustomerResolver.get_customer_ltv(info, self.id, self.store_id)
    
    @strawberry.field
    async def tags(self, info) -> Optional[List[str]]:
        from app.api.graphql.customers.resolvers import CustomerResolver
        return await CustomerResolver.get_customer_tags(self.id, info)

@strawberry.type
class CustomerLtvMetrics:
    """Type representing customer lifetime value metrics."""
    customer_id: ID
    total_orders: int
    total_spent: Numeric
    total_profit: Numeric
    net_profit_ltv: Numeric
    average_order_value: Numeric
    average_profit_per_order: Numeric
    first_order_date: Date
    last_order_date: Date
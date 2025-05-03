from typing import Optional, List
import strawberry
from strawberry.scalars import ID
from app.api.graphql.types.scalars import DateTime, Numeric
from app.api.graphql.common.inputs import DateRangeInput

@strawberry.type
class Customer:
    id: ID
    platform_customer_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    orders_count: int
    total_spent: Numeric
    platform_created_at: Optional[DateTime] = None
    platform_updated_at: Optional[DateTime] = None
    synced_at: DateTime
    
    @strawberry.field
    def average_order_value(self) -> Numeric:
        if self.orders_count > 0:
            return self.total_spent / self.orders_count
        return 0
    
    @strawberry.field
    async def date_of_last_order(self, info) -> Optional[DateTime]:
        from app.api.graphql.customers.resolvers import CustomerResolver
        return await CustomerResolver.get_customer_last_order_date(self.id, info)
        
  
    
    @strawberry.field
    async def lifetime_value(self, info) -> Numeric:
        from app.api.graphql.customers.resolvers import resolve_customer_lifetime_value
        return await resolve_customer_lifetime_value(self.id, info)
    
    @strawberry.field
    async def tags(self, info) -> Optional[List[str]]:
        from app.api.graphql.customers.resolvers import resolve_customer_tags
        return await resolve_customer_tags(self.id, info)
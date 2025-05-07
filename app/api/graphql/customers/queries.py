import strawberry
from typing import Optional
from app.api.graphql.customers.connection import CustomerConnection
from strawberry.types import Info
from app.api.graphql.customers.types import CustomerLtvMetrics
from app.api.graphql.permissions import StoreOwnerPermission
@strawberry.type
class CustomerQuery:
    @strawberry.field(permission_classes=[StoreOwnerPermission])
    async def customers_connection(
        self, 
        info: Info, 
        store_id: strawberry.ID, 
        first: int = 10, 
        after: Optional[str] = None
    ) -> CustomerConnection:
        """Get a paginated list of customers."""
        from app.api.graphql.customers.resolvers import CustomerResolver
        db = CustomerResolver.get_db_from_info(info)
        return await CustomerResolver.get_customers_connection(
            store_id=store_id,
            first=first,
            after=after,
            db=db
        )
    @strawberry.field(permission_classes=[StoreOwnerPermission])
    async def customer_ltv(
        self,
        info,
        customer_id: strawberry.ID,
        store_id: strawberry.ID,
    ) -> CustomerLtvMetrics:
        from app.api.graphql.customers.resolvers import CustomerResolver
        return await CustomerResolver.get_customer_ltv(
            info,
            customer_id,
            store_id
        )
        
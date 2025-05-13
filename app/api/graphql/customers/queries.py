import strawberry
from typing import Optional
from app.api.graphql.customers.connection import CustomerConnection
from app.api.graphql.customers.types import Customer
from strawberry.types import Info
from app.api.graphql.permissions import StoreOwnerPermission
@strawberry.type
class CustomerQuery:
    @strawberry.field(permission_classes=[StoreOwnerPermission])
    async def customer(self, info: Info, id: strawberry.ID,store_id: strawberry.ID) -> Optional[Customer]:
        """Get a customer by ID."""
        from app.api.graphql.customers.resolvers import CustomerResolver
        db = CustomerResolver.get_db_from_info(info)
        customer_model = await CustomerResolver.get_by_id(id, db)
        if not customer_model:
            return None
        return CustomerResolver.to_graphql_type(customer_model)
    
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
    

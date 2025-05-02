import strawberry
from typing import Optional
from strawberry.scalars import ID
from app.api.graphql.customers.connection import CustomerConnection
from app.api.graphql.common.inputs import DateRangeInput

@strawberry.type
class CustomerQuery:
    @strawberry.field
    async def customers(
        self, 
        info, 
        store_id: ID, 
        limit: int = 20, 
        offset: int = 0, 
        sort_by: Optional[str] = None, 
        sort_desc: bool = False, 
        search: Optional[str] = None
    ) -> CustomerConnection:
        from app.api.graphql.customers.resolvers import resolve_customers
        return await resolve_customers(info, store_id, limit, offset, sort_by, sort_desc, search)
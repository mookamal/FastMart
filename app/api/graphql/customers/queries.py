import strawberry
from typing import Optional
from strawberry.scalars import ID
from app.api.graphql.customers.connection import CustomerConnection
from app.api.graphql.common.inputs import DateRangeInput
from app.api.graphql.common.connection import Connection
@strawberry.type
class CustomerQuery:
    pass
    # @strawberry.field
    # async def customers_connection(
    #     self, 
    #     info: Info, 
    #     store_id: strawberry.ID, 
    #     first: int = 10, 
    #     after: Optional[str] = None
    # ) -> CustomerConnection:
    #     """Get a paginated list of customers."""
    #     from app.api.graphql.customers.resolvers import CustomerResolver
    #     db = CustomerResolver.get_db_from_info(info)
    #     return await CustomerResolver.get_customers_connection(
    #         store_id=store_id,
    #         first=first,
    #         after=after,
    #         db=db
    #     )
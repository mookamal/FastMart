
from typing import List
import strawberry
from strawberry.scalars import ID
from strawberry.types import Info
from app.api.graphql.types.scalars import DateTime
from app.api.graphql.stores.types import Store

@strawberry.type
class User:
    id: ID
    email: str
    created_at: DateTime
    
    @strawberry.field
    async def stores(self, info: Info) -> List["Store"]:
        from app.api.graphql.resolvers.user_resolver import resolve_user_stores
        return await resolve_user_stores(self, info)
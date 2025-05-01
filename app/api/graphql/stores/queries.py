import strawberry
from strawberry.types import Info
from strawberry.scalars import ID
from app.api.graphql.stores.types import Store

@strawberry.type
class StoreQuery:
    @strawberry.field
    async def store(self, info: Info, id: ID) -> Store:
        from app.api.graphql.resolvers.store_resolver import resolve_store
        return await resolve_store(info, id)
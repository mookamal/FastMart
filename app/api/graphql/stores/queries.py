import strawberry
from strawberry.types import Info
from strawberry.scalars import ID
from app.api.graphql.stores.types import Store
from app.api.graphql.permissions import StoreOwnerPermission

@strawberry.type
class StoreQuery:
    @strawberry.field(permission_classes=[StoreOwnerPermission])
    async def store(self, info: Info, store_id: ID) -> Store:
        from app.api.graphql.stores.resolvers import resolve_store
        return await resolve_store(info, store_id)
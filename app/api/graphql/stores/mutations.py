import strawberry
from strawberry.types import Info
from strawberry.scalars import ID
from app.api.graphql.stores.types import Store

@strawberry.type
class StoreMutation:
    @strawberry.mutation
    async def gen_link_shopify(self, info: Info, shop_domain: str) -> str:
        from app.api.graphql.resolvers.mutation_resolver import resolve_gen_link_shopify
        return await resolve_gen_link_shopify(info, shop_domain)
    
    @strawberry.mutation
    async def connect_shopify_store(
        self, 
        info: Info, 
        authorization_code: str, 
        shop_domain: str
    ) -> Store:
        from app.api.graphql.resolvers.mutation_resolver import resolve_connect_shopify_store
        return await resolve_connect_shopify_store(info, authorization_code, shop_domain)
    
    @strawberry.mutation
    async def disconnect_store(
        self, 
        info: Info, 
        store_id: ID
    ) -> bool:
        from app.api.graphql.resolvers.mutation_resolver import resolve_disconnect_store
        return await resolve_disconnect_store(info, store_id)
    
    @strawberry.mutation
    async def trigger_store_sync(
        self, 
        info: Info, 
        store_id: ID
    ) -> bool:
        from app.api.graphql.resolvers.mutation_resolver import resolve_trigger_store_sync
        return await resolve_trigger_store_sync(info, store_id)
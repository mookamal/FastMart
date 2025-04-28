import decimal
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

import strawberry
from strawberry.scalars import ID
from strawberry.types import Info

# Define scalar types
DateTime = strawberry.scalar(
    datetime,
    description="ISO-8601 formatted datetime",
    serialize=lambda v: v.isoformat(),
    parse_value=lambda v: datetime.fromisoformat(v),
)

Date = strawberry.scalar(
    date,
    description="ISO-8601 formatted date",
    serialize=lambda v: v.isoformat(),
    parse_value=lambda v: date.fromisoformat(v),
)

Numeric = strawberry.scalar(
    decimal.Decimal,
    description="Decimal number",
    serialize=lambda v: str(v),
    parse_value=lambda v: decimal.Decimal(v),
)

# Define GraphQL types
@strawberry.type
class User:
    id: ID
    email: str
    created_at: DateTime
    
    @strawberry.field
    async def stores(self, info: Info) -> List["Store"]:
        from app.api.graphql.resolvers.user_resolver import resolve_user_stores
        return await resolve_user_stores(self, info)

@strawberry.type
class Store:
    id: ID
    platform: str
    shop_domain: str
    is_active: bool
    last_sync_at: Optional[DateTime] = None
    created_at: DateTime
    
    @strawberry.field
    async def products(self, info: Info) -> List["Product"]:
        from app.api.graphql.resolvers.store_resolver import resolve_store_products
        return await resolve_store_products(self, info)
    
    @strawberry.field
    async def customers(self, info: Info) -> List["Customer"]:
        from app.api.graphql.resolvers.store_resolver import resolve_store_customers
        return await resolve_store_customers(self, info)
    
    @strawberry.field
    async def orders(self, info: Info) -> List["Order"]:
        from app.api.graphql.resolvers.store_resolver import resolve_store_orders
        return await resolve_store_orders(self, info)

@strawberry.type
class Product:
    id: ID
    platform_product_id: str
    title: str
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    platform_created_at: Optional[DateTime] = None
    platform_updated_at: Optional[DateTime] = None
    synced_at: DateTime

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

@strawberry.type
class Order:
    id: ID
    platform_order_id: str
    order_number: str
    total_price: Numeric
    currency: str
    financial_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    processed_at: Optional[DateTime] = None
    platform_created_at: DateTime
    platform_updated_at: Optional[DateTime] = None
    synced_at: DateTime

# Define root Query type
@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info: Info) -> User:
        from app.api.graphql.resolvers.user_resolver import resolve_me
        return await resolve_me(info)
    
    @strawberry.field
    async def store(self, info: Info, id: ID) -> Store:
        from app.api.graphql.resolvers.store_resolver import resolve_store
        return await resolve_store(info, id)

# Define root Mutation type
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def gen_link_shopify(self,info: Info,shop_domain: str) -> str:
        from app.api.graphql.resolvers.mutation_resolver import resolve_gen_link_shopify
        return await resolve_gen_link_shopify(info,shop_domain)
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

# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
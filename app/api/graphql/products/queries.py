import strawberry
from typing import Optional, List
from strawberry.types import Info
from app.api.graphql.products.types import Product
from app.api.graphql.common.connection import Connection
from app.api.graphql.permissions import StoreOwnerPermission

@strawberry.type
class ProductQuery:
    @strawberry.field(permission_classes=[StoreOwnerPermission])
    async def product(self, info: Info, id: strawberry.ID) -> Optional[Product]:
        """Get a product by ID."""
        from app.api.graphql.products.resolvers import ProductResolver
        db = ProductResolver.get_db_from_info(info)
        product_model = await ProductResolver.get_by_id(id, db)
        if not product_model:
            return None
        return ProductResolver.to_graphql_type(product_model)
    
    @strawberry.field(permission_classes=[StoreOwnerPermission])
    async def products(self, info: Info, store_id: strawberry.ID) -> List[Product]:
        """Get all products for a store."""
        from app.api.graphql.products.resolvers import ProductResolver
        db = ProductResolver.get_db_from_info(info)
        return await ProductResolver.get_products_by_store_id(store_id, db)
    
    @strawberry.field(permission_classes=[StoreOwnerPermission])
    async def products_connection(
        self, 
        info: Info, 
        store_id: strawberry.ID, 
        first: int = 10, 
        after: Optional[str] = None
    ) -> Connection[Product]:
        """Get a paginated connection of products."""
        from app.api.graphql.products.resolvers import ProductResolver
        db = ProductResolver.get_db_from_info(info)
        return await ProductResolver.get_product_connection(store_id, first, after, db)
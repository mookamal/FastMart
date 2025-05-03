from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info

from app.db.models.product import Product as ProductModel
from app.api.graphql.products.types import Product
from app.api.graphql.resolvers import BaseResolver
from app.api.graphql.common.connection import Connection, Edge, PageInfo, encode_cursor, decode_cursor

class ProductResolver(BaseResolver[ProductModel, Product]):
    """Resolver for Product-related operations."""
    
    model_class = ProductModel
    graphql_type_class = Product
    
    @classmethod
    def to_graphql_type(cls, model: ProductModel) -> Product:
        """Convert a ProductModel to a GraphQL Product type."""
        return Product(
            id=str(model.id),
            platform_product_id=model.platform_product_id,
            title=model.title,
            vendor=model.vendor,
            product_type=model.product_type,
            platform_created_at=model.platform_created_at,
            platform_updated_at=model.platform_updated_at,
            synced_at=model.synced_at
        )
    
    @classmethod
    async def get_products_by_store_id(cls, store_id: str, db: AsyncSession) -> List[Product]:
        """Get all products for a specific store."""
        try:
            store_uuid = UUID(store_id)
            query = select(cls.model_class).where(cls.model_class.store_id == store_uuid)
            result = await db.execute(query)
            product_models = result.scalars().all()
            
            return [cls.to_graphql_type(model) for model in product_models]
        except Exception as e:
            raise ValueError(f"Error retrieving products: {str(e)}")
    
    @classmethod
    async def get_product_connection(cls, store_id: str, first: int, after: Optional[str], db: AsyncSession) -> Connection[Product]:
        """Get a paginated connection of products."""
        try:
            store_uuid = UUID(store_id)
            query = select(cls.model_class).where(cls.model_class.store_id == store_uuid)
            
            # Apply cursor-based pagination
            if after:
                cursor_value = decode_cursor(after)
                # Assuming cursor is the product ID
                query = query.where(cls.model_class.id > UUID(cursor_value))
            
            # Apply limit
            query = query.limit(first + 1)  # +1 to check if there's a next page
            
            result = await db.execute(query)
            product_models = result.scalars().all()
            
            # Check if there's a next page
            has_next_page = len(product_models) > first
            if has_next_page:
                product_models = product_models[:first]  # Remove the extra item
            
            # Create edges
            edges = []
            for model in product_models:
                product = cls.to_graphql_type(model)
                cursor = encode_cursor(str(model.id))
                edges.append(Edge(node=product, cursor=cursor))
            
            # Create page info
            start_cursor = edges[0].cursor if edges else None
            end_cursor = edges[-1].cursor if edges else None
            page_info = PageInfo(
                has_next_page=has_next_page,
                has_previous_page=after is not None,
                start_cursor=start_cursor,
                end_cursor=end_cursor
            )
            
            # Get total count
            count_query = select(cls.model_class).where(cls.model_class.store_id == store_uuid)
            count_result = await db.execute(count_query)
            total_count = len(count_result.scalars().all())
            
            return Connection(
                edges=edges,
                page_info=page_info,
                total_count=total_count
            )
        except Exception as e:
            raise ValueError(f"Error retrieving product connection: {str(e)}")
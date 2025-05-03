from typing import List
import strawberry
from app.api.graphql.products.types import Product
from app.api.graphql.common.connection import Connection, Edge, PageInfo

# Type aliases for Product connections
ProductEdge = Edge[Product]
ProductConnection = Connection[Product]

# Re-export these types for backward compatibility
__all__ = ['ProductEdge', 'ProductConnection', 'PageInfo']
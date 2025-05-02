from typing import List, Optional
import strawberry
from strawberry.scalars import ID
from app.api.graphql.products.types import Product

@strawberry.type
class ProductEdge:
    node: Product
    cursor: str

@strawberry.type
class ProductConnection:
    edges: List[ProductEdge]
    total_count: int
    page_info: "PageInfo"

@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None
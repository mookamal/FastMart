from typing import List, Optional
import strawberry
from strawberry.scalars import ID
from app.api.graphql.customers.types import Customer

@strawberry.type
class CustomerEdge:
    node: Customer
    cursor: str

@strawberry.type
class CustomerConnection:
    edges: List[CustomerEdge]
    total_count: int
    page_info: "PageInfo"

@strawberry.type
class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None
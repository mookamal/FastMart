from typing import TypeVar, Generic
from strawberry.scalars import ID
import strawberry

# Common types that can be shared across features

@strawberry.type
class PageInfo:
    """Information about pagination in a connection."""
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str
    end_cursor: str

T = TypeVar('T')

@strawberry.type
class Edge(Generic[T]):
    """An edge in a connection."""
    node: T
    cursor: str

@strawberry.type
class Connection(Generic[T]):
    """A connection to a list of items."""
    edges: list[Edge[T]]
    page_info: PageInfo
    total_count: int
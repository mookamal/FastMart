from typing import TypeVar, Generic, List, Optional
import strawberry
from strawberry.scalars import ID

T = TypeVar('T')  # Type for the node in the connection

@strawberry.type
class PageInfo:
    """Information about pagination in a connection."""
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None

@strawberry.type
class Edge(Generic[T]):
    """An edge in a connection."""
    node: T
    cursor: str

@strawberry.type
class Connection(Generic[T]):
    """A connection to a list of items."""
    edges: List[Edge[T]]
    page_info: PageInfo
    total_count: int

# Helper functions for pagination
def encode_cursor(value: str) -> str:
    """Encode a cursor value."""
    import base64
    return base64.b64encode(value.encode()).decode()

def decode_cursor(cursor: str) -> str:
    """Decode a cursor value."""
    import base64
    return base64.b64decode(cursor.encode()).decode()
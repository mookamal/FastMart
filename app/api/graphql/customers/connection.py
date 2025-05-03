from typing import List
import strawberry
from app.api.graphql.customers.types import Customer
from app.api.graphql.common.connection import Connection, Edge, PageInfo

# Type aliases for Customer connections
CustomerEdge = Edge[Customer]
CustomerConnection = Connection[Customer]

# Re-export these types for backward compatibility
__all__ = ['CustomerEdge', 'CustomerConnection', 'PageInfo']
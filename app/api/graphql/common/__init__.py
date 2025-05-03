# Common module for shared Strawberry elements across features
from app.api.graphql.common.connection import Connection, Edge, PageInfo, encode_cursor, decode_cursor
from app.api.graphql.common.types import Connection as DeprecatedConnection, Edge as DeprecatedEdge, PageInfo as DeprecatedPageInfo

__all__ = [
    'Connection', 'Edge', 'PageInfo', 'encode_cursor', 'decode_cursor',
    # Keep deprecated types for backward compatibility
    'DeprecatedConnection', 'DeprecatedEdge', 'DeprecatedPageInfo'
]
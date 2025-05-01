from typing import Optional
import strawberry
from strawberry.scalars import ID
from app.api.graphql.types.scalars import DateTime

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
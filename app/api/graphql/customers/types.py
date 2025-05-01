from typing import Optional
import strawberry
from strawberry.scalars import ID
from app.api.graphql.types.scalars import DateTime,Numeric

@strawberry.type
class Customer:
    id: ID
    platform_customer_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    orders_count: int
    total_spent: Numeric
    platform_created_at: Optional[DateTime] = None
    platform_updated_at: Optional[DateTime] = None
    synced_at: DateTime
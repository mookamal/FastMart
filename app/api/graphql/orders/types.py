from typing import Optional
import strawberry
from strawberry.scalars import ID
from app.api.graphql.types.scalars import DateTime, Numeric

@strawberry.type
class Order:
    id: ID
    platform_order_id: str
    order_number: str
    total_price: Numeric
    currency: str
    financial_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    processed_at: Optional[DateTime] = None
    platform_created_at: DateTime
    platform_updated_at: Optional[DateTime] = None
    synced_at: DateTime
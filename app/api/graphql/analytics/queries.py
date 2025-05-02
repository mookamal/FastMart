import strawberry
from typing import Optional, List
from app.api.graphql.common.inputs import DateRangeInput
from app.api.graphql.analytics.types import ProductVariantAnalytics
@strawberry.type
class AnalyticsQuery:
    @strawberry.field
    async def product_variant_analytics(
        self, 
        info, 
        store_id: strawberry.ID, 
        date_range: Optional[DateRangeInput] = None
    ) -> List[ProductVariantAnalytics]:
        from app.api.graphql.analytics.resolvers import resolve_product_variant_analytics
        return await resolve_product_variant_analytics(store_id, date_range, info)
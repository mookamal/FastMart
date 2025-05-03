import strawberry
from typing import Optional, List
from app.api.graphql.common.inputs import DateRangeInput
from app.api.graphql.analytics.types import ProductVariantAnalytics, DiscountCodeAnalytics
from app.api.graphql.analytics.profit_types import ProfitMetrics
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

    @strawberry.field
    async def discount_code_analytics(
        self,
        info,
        store_id: strawberry.ID,
        date_range: Optional[DateRangeInput] = None,
        limit: int = 20,
    ) -> List[DiscountCodeAnalytics]:
        from app.api.graphql.analytics.resolvers import resolve_discount_code_analytics
        return await resolve_discount_code_analytics(info, store_id, date_range, limit)
        
    @strawberry.field
    async def profit_metrics(
        self,
        info,
        store_id: strawberry.ID,
        date_range: DateRangeInput,
    ) -> ProfitMetrics:
        from app.api.graphql.analytics.profit_resolvers import resolve_profit_metrics
        return await resolve_profit_metrics(info, store_id, date_range)
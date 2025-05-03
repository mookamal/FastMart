import strawberry
from typing import Optional, List
from app.api.graphql.common.inputs import DateRangeInput
from app.api.graphql.analytics.types import ProductVariantAnalytics, DiscountCodeAnalytics, AdSpend, OtherCost
from app.api.graphql.analytics.net_profit_types import NetProfitMetrics, PnlReport, CustomerLtvMetrics
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
    async def net_profit_analytics(
        self,
        info,
        store_id: strawberry.ID,
        date_range: DateRangeInput,
    ) -> NetProfitMetrics:
        from app.api.graphql.analytics.net_profit_resolvers import resolve_net_profit_analytics
        return await resolve_net_profit_analytics(info, store_id, date_range)
    
    @strawberry.field
    async def profit_and_loss_report(
        self,
        info,
        store_id: strawberry.ID,
        date_range: DateRangeInput,
    ) -> PnlReport:
        from app.api.graphql.analytics.net_profit_resolvers import resolve_profit_and_loss_report
        return await resolve_profit_and_loss_report(info, store_id, date_range)
    
    @strawberry.field
    async def customer_ltv(
        self,
        info,
        customer_id: strawberry.ID,
        store_id: strawberry.ID,
    ) -> CustomerLtvMetrics:
        from app.api.graphql.analytics.net_profit_resolvers import resolve_customer_ltv
        return await resolve_customer_ltv(info, customer_id, store_id)
    
    @strawberry.field
    async def ad_spend_entries(
        self,
        info,
        store_id: strawberry.ID,
        date_range: Optional[DateRangeInput] = None,
    ) -> List[AdSpend]:
        from app.api.graphql.analytics.net_profit_resolvers import resolve_ad_spend_entries
        return await resolve_ad_spend_entries(info, store_id, date_range)
    
    @strawberry.field
    async def other_cost_entries(
        self,
        info,
        store_id: strawberry.ID,
    ) -> List[OtherCost]:
        from app.api.graphql.analytics.net_profit_resolvers import resolve_other_cost_entries
        return await resolve_other_cost_entries(info, store_id)
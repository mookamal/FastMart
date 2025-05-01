import strawberry
from app.api.graphql.types.scalars import  Numeric, Date
from app.api.graphql.products.types import Product

@strawberry.type
class AnalyticsSummary:
    total_sales: Numeric
    order_count: int
    average_order_value: Numeric
    new_customer_count: int

@strawberry.type
class ProductAnalytics:
    product: "Product"
    total_quantity_sold: int
    total_revenue: Numeric

@strawberry.type
class TimeSeriesDataPoint:
    date: Date
    value: Numeric
from typing import List
from uuid import UUID
from sqlalchemy import func, select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info

from app.db.models.order import Order as OrderModel
from app.db.models.customer import Customer as CustomerModel
from app.db.models.product import Product as ProductModel
from app.db.models.line_item import LineItem as LineItemModel
from app.api.graphql.schema import AnalyticsSummary, ProductAnalytics, TimeSeriesDataPoint, Product, TimeInterval


async def resolve_analytics_summary(store_id: str, date_range, info: Info) -> AnalyticsSummary:
    """Resolver for the analyticsSummary field on the Store type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    store_uuid = UUID(store_id)
    
    # Query for total sales and order count
    sales_query = select(
        func.sum(OrderModel.total_price).label("total_sales"),
        func.count(OrderModel.id).label("order_count"),
        func.coalesce(func.avg(OrderModel.total_price), 0).label("average_order_value")
    ).where(
        and_(
            OrderModel.store_id == store_uuid,
            OrderModel.processed_at >= date_range.start_date,
            OrderModel.processed_at <= date_range.end_date
        )
    )
    
    sales_result = await db.execute(sales_query)
    sales_data = sales_result.fetchone()
    
    # Query for new customer count
    new_customers_query = select(func.count(CustomerModel.id)).where(
        and_(
            CustomerModel.store_id == store_uuid,
            CustomerModel.platform_created_at >= date_range.start_date,
            CustomerModel.platform_created_at <= date_range.end_date
        )
    )
    
    new_customers_result = await db.execute(new_customers_query)
    new_customer_count = new_customers_result.scalar() or 0
    
    # Return the analytics summary
    return AnalyticsSummary(
        total_sales=sales_data.total_sales or 0,
        order_count=sales_data.order_count or 0,
        average_order_value=sales_data.average_order_value or 0,
        new_customer_count=new_customer_count
    )


async def resolve_top_selling_products(store_id: str, date_range, limit: int, info: Info) -> List[ProductAnalytics]:
    """Resolver for the topSellingProducts field on the Store type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    store_uuid = UUID(store_id)
    
    # Query for top selling products
    query = select(
        LineItemModel.product_id,
        func.sum(LineItemModel.quantity).label("total_quantity"),
        func.sum(LineItemModel.quantity * LineItemModel.price).label("total_revenue")
    ).join(
        OrderModel, LineItemModel.order_id == OrderModel.id
    ).where(
        and_(
            OrderModel.store_id == store_uuid,
            OrderModel.processed_at >= date_range.start_date,
            OrderModel.processed_at <= date_range.end_date,
            LineItemModel.product_id.is_not(None)  # Ensure product_id is not null
        )
    ).group_by(
        LineItemModel.product_id
    ).order_by(
        desc("total_quantity")
    ).limit(limit)
    
    result = await db.execute(query)
    top_products_data = result.fetchall()
    
    # Get product details for each top product
    product_analytics_list = []
    for product_data in top_products_data:
        product_id = product_data.product_id
        
        # Get product details
        product_query = select(ProductModel).where(ProductModel.id == product_id)
        product_result = await db.execute(product_query)
        product_model = product_result.scalar_one_or_none()
        
        if product_model:
            # Create Product GraphQL type
            product = Product(
                id=str(product_model.id),
                platform_product_id=product_model.platform_product_id,
                title=product_model.title,
                vendor=product_model.vendor,
                product_type=product_model.product_type,
                platform_created_at=product_model.platform_created_at,
                platform_updated_at=product_model.platform_updated_at,
                synced_at=product_model.synced_at
            )
            
            # Create ProductAnalytics GraphQL type
            product_analytics = ProductAnalytics(
                product=product,
                total_quantity_sold=product_data.total_quantity,
                total_revenue=product_data.total_revenue
            )
            
            product_analytics_list.append(product_analytics)
    
    return product_analytics_list


async def resolve_orders_over_time(store_id: str, date_range, interval: TimeInterval, info: Info) -> List[TimeSeriesDataPoint]:
    """Resolver for the ordersOverTime field on the Store type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    store_uuid = UUID(store_id)
    
    # Determine the date truncation function based on the interval
    if interval == TimeInterval.DAY:
        date_trunc_func = func.date_trunc('day', OrderModel.processed_at)
    elif interval == TimeInterval.WEEK:
        date_trunc_func = func.date_trunc('week', OrderModel.processed_at)
    elif interval == TimeInterval.MONTH:
        date_trunc_func = func.date_trunc('month', OrderModel.processed_at)
    else:
        date_trunc_func = func.date_trunc('day', OrderModel.processed_at)
    
    # Query for orders over time
    query = select(
        date_trunc_func.label("date"),
        func.sum(OrderModel.total_price).label("value")
    ).where(
        and_(
            OrderModel.store_id == store_uuid,
            OrderModel.processed_at >= date_range.start_date,
            OrderModel.processed_at <= date_range.end_date
        )
    ).group_by(
        "date"
    ).order_by(
        "date"
    )
    
    result = await db.execute(query)
    time_series_data = result.fetchall()
    
    # Convert to TimeSeriesDataPoint GraphQL type
    return [
        TimeSeriesDataPoint(
            date=data.date.date(),  # Convert datetime to date
            value=data.value or 0
        ) for data in time_series_data
    ]
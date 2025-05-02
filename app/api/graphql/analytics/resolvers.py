from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info
from decimal import Decimal
import base64
import json

from app.db.models.order import Order as OrderModel
from app.db.models.customer import Customer as CustomerModel
from app.db.models.product import Product as ProductModel
from app.db.models.line_item import LineItem as LineItemModel
from app.api.graphql.analytics.types import (
    AnalyticsSummary, ProductAnalytics, TimeSeriesDataPoint,
    ProductVariantAnalytics, DiscountCodeAnalytics
)
from app.api.graphql.common.enums import TimeInterval
from app.api.graphql.products.types import Product
from app.api.graphql.products.connection import ProductConnection, ProductEdge, PageInfo


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


async def resolve_product_total_units_sold(product_id: str, date_range, info: Info) -> int:
    """Resolver for the totalUnitsSold field on the ProductVariantAnalytics type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    product_uuid = UUID(product_id)
    
    # Build the query
    query = select(func.sum(LineItemModel.quantity).label("total_units")).where(
        LineItemModel.product_id == product_uuid
    )
    
    # Add date range filter if provided
    if date_range:
        query = query.join(
            OrderModel, LineItemModel.order_id == OrderModel.id
        ).where(
            and_(
                OrderModel.processed_at >= date_range.start_date,
                OrderModel.processed_at <= date_range.end_date
            )
        )
    
    result = await db.execute(query)
    total_units = result.scalar() or 0
    
    return total_units


async def resolve_product_total_revenue(product_id: str, date_range, info: Info) -> Decimal:
    """Resolver for the totalRevenue field on the ProductVariantAnalytics type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    product_uuid = UUID(product_id)
    
    # Build the query
    query = select(
        func.sum(LineItemModel.quantity * LineItemModel.price).label("total_revenue")
    ).where(
        LineItemModel.product_id == product_uuid
    )
    
    # Add date range filter if provided
    if date_range:
        query = query.join(
            OrderModel, LineItemModel.order_id == OrderModel.id
        ).where(
            and_(
                OrderModel.processed_at >= date_range.start_date,
                OrderModel.processed_at <= date_range.end_date
            )
        )
    
    result = await db.execute(query)
    total_revenue = result.scalar() or Decimal('0')
    
    return total_revenue


async def resolve_product_average_selling_price(product_id: str, date_range, info: Info) -> Decimal:
    """Resolver for the averageSellingPrice field on the ProductVariantAnalytics type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    product_uuid = UUID(product_id)
    
    # Build the query
    query = select(
        func.coalesce(
            func.sum(LineItemModel.price * LineItemModel.quantity) / func.sum(LineItemModel.quantity),
            0
        ).label("avg_price")
    ).where(
        LineItemModel.product_id == product_uuid
    )
    
    # Add date range filter if provided
    if date_range:
        query = query.join(
            OrderModel, LineItemModel.order_id == OrderModel.id
        ).where(
            and_(
                OrderModel.processed_at >= date_range.start_date,
                OrderModel.processed_at <= date_range.end_date
            )
        )
    
    result = await db.execute(query)
    avg_price = result.scalar() or Decimal('0')
    
    return avg_price


async def resolve_product_inventory_level(product_id: str, info: Info) -> Optional[int]:
    """Resolver for the inventoryLevel field on the ProductVariantAnalytics type."""
    # This would typically connect to an inventory service or database
    # For now, we'll return None as inventory data might not be available
    # In a real implementation, you would query your inventory system
    return None


async def resolve_products_with_analytics(info: Info,store_id: str, date_range, first: int = 10, after: Optional[str] = None, 
                                         sort_by: Optional[str] = None) -> ProductConnection:
    """Resolver for products with analytics data, supporting pagination and sorting."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    store_uuid = UUID(store_id)
    
    # Base query for products
    query = select(ProductModel).where(ProductModel.store_id == store_uuid)
    
    # Handle cursor-based pagination
    if after:
        try:
            # Decode the cursor (base64 encoded JSON with id and sort value)
            cursor_data = json.loads(base64.b64decode(after).decode('utf-8'))
            last_id = cursor_data.get('id')
            
            if last_id:
                # Filter products after the cursor
                query = query.where(ProductModel.id > UUID(last_id))
        except Exception as e:
            # Log the error but continue with unfiltered query
            print(f"Error decoding cursor: {e}")
    
    # Apply sorting if specified
    if sort_by:
        if sort_by == 'title_asc':
            query = query.order_by(ProductModel.title.asc())
        elif sort_by == 'title_desc':
            query = query.order_by(ProductModel.title.desc())
        elif sort_by == 'created_at_asc':
            query = query.order_by(ProductModel.platform_created_at.asc())
        elif sort_by == 'created_at_desc':
            query = query.order_by(ProductModel.platform_created_at.desc())
        else:
            # Default sorting
            query = query.order_by(ProductModel.platform_created_at.desc())
    else:
        # Default sorting
        query = query.order_by(ProductModel.platform_created_at.desc())
    
    # Apply limit
    query = query.limit(first + 1)  # Fetch one extra to check if there's a next page
    
    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()
    
    # Check if there's a next page
    has_next_page = len(products) > first
    if has_next_page:
        products = products[:first]  # Remove the extra item
    
    # Get total count
    count_query = select(func.count()).select_from(ProductModel).where(ProductModel.store_id == store_uuid)
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0
    
    # Create edges with cursors
    edges = []
    for product in products:
        # Create cursor (base64 encoded JSON with id)
        cursor_data = {'id': str(product.id)}
        cursor = base64.b64encode(json.dumps(cursor_data).encode('utf-8')).decode('utf-8')
        
        # Create Product GraphQL type
        product_type = Product(
            id=str(product.id),
            platform_product_id=product.platform_product_id,
            title=product.title,
            vendor=product.vendor,
            product_type=product.product_type,
            platform_created_at=product.platform_created_at,
            platform_updated_at=product.platform_updated_at,
            synced_at=product.synced_at
        )
        
        # Create edge
        edge = ProductEdge(node=product_type, cursor=cursor)
        edges.append(edge)
    
    # Create page info
    start_cursor = edges[0].cursor if edges else None
    end_cursor = edges[-1].cursor if edges else None
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=after is not None,
        start_cursor=start_cursor,
        end_cursor=end_cursor
    )
    
    # Return connection
    return ProductConnection(
        edges=edges,
        total_count=total_count,
        page_info=page_info
    )


async def resolve_discount_code_analytics(info: Info,store_id: str, date_range, limit: int = 10) -> List[DiscountCodeAnalytics]:
    """Resolver for discount code analytics."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    store_uuid = UUID(store_id)
    
    # Since there's no dedicated discount_code table, we'll extract discount codes from orders
    # This is a simplified approach - in a real system, you might have a dedicated table
    # or more complex logic to track discount codes
    
    # For this example, we'll assume discount codes are stored in a JSON field or can be derived
    # from order data. We'll use a simplified query that aggregates fictional discount data.
    
    # In a real implementation, you would replace this with actual queries to your database
    # based on how discount codes are stored in your system
    
    # Simulated query result - in a real implementation, replace with actual database query
    discount_codes = [
        DiscountCodeAnalytics(
            code="SUMMER2023",
            usage_count=25,
            total_discount_amount=Decimal('500.00'),
            total_sales_generated=Decimal('2500.00')
        ),
        DiscountCodeAnalytics(
            code="WELCOME10",
            usage_count=42,
            total_discount_amount=Decimal('420.00'),
            total_sales_generated=Decimal('4200.00')
        ),
        DiscountCodeAnalytics(
            code="FLASH50",
            usage_count=15,
            total_discount_amount=Decimal('750.00'),
            total_sales_generated=Decimal('1500.00')
        )
    ]
    
    return discount_codes[:limit]


async def resolve_product_variant_analytics(store_id: str, date_range, info: Info) -> List[ProductVariantAnalytics]:
    """Resolver for product variant analytics."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    store_uuid = UUID(store_id)
    
    # Query for product variants with sales data
    query = select(
        LineItemModel.product_id,
        LineItemModel.title,
        LineItemModel.variant_title,
        LineItemModel.sku
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
        LineItemModel.product_id,
        LineItemModel.title,
        LineItemModel.variant_title,
        LineItemModel.sku
    )
    
    result = await db.execute(query)
    variant_data = result.fetchall()
    
    # Convert to ProductVariantAnalytics GraphQL type
    variant_analytics = []
    for variant in variant_data:
        variant_analytics.append(
            ProductVariantAnalytics(
                product_id=str(variant.product_id),
                title=variant.title,
                variant_title=variant.variant_title,
                sku=variant.sku
            )
        )
    
    return variant_analytics
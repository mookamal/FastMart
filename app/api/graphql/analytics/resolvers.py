from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info
from decimal import Decimal, InvalidOperation
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
    """Resolver for the inventoryLevel field on the ProductVariantAnalytics type.
    
    Retrieves the total inventory level for a product by summing up the available
    inventory across all variants from the product's inventory_levels JSONB field.
    
    Args:
        product_id: The ID of the product to get inventory for
        info: The GraphQL resolver info object containing context
        
    Returns:
        The total inventory count or None if inventory data is not available
    """
    context = info.context
    db: AsyncSession = context["db"]
    
    try:
        # Query the product to get its inventory_levels
        result = await db.execute(
            select(ProductModel.inventory_levels)
            .where(ProductModel.id == product_id)
        )
        inventory_data = result.scalar_one_or_none()
        
        if not inventory_data:
            return None
        
        # Calculate total inventory by summing up available quantities across all variants
        total_inventory = 0
        for variant_id, variant_data in inventory_data.items():
            # Each variant_data should have an 'available' field with the inventory count
            if isinstance(variant_data, dict) and 'available' in variant_data:
                try:
                    available = int(variant_data['available'])
                    total_inventory += available
                except (ValueError, TypeError):
                    # Skip variants with invalid inventory values
                    continue
        
        return total_inventory
    except Exception as e:
        # Log the error but don't raise it to the client
        logger.error(f"Error retrieving inventory level for product {product_id}: {e}")
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


async def resolve_discount_code_analytics(info: Info, store_id: str, date_range, limit: int = 10) -> List[DiscountCodeAnalytics]:
    """Resolver for discount code analytics."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    store_uuid = UUID(store_id)
    
    # Convert date strings to datetime objects with timezone info for proper comparison
    from datetime import datetime, timezone
    
    # Create datetime objects at the start and end of the day with timezone info
    # Use timezone.utc to ensure proper comparison with database timestamps
    start_date = datetime.combine(date_range.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_date = datetime.combine(date_range.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    # First check if there are any orders in the date range regardless of discount
    all_orders_query = select(func.count(OrderModel.id)).where(
        and_(
            OrderModel.store_id == store_uuid,
            OrderModel.processed_at >= start_date,
            OrderModel.processed_at <= end_date
        )
    )
    
    # Query orders within the date range (don't filter by discount_applications yet)
    query = select(OrderModel).where(
        and_(
            OrderModel.store_id == store_uuid,
            OrderModel.processed_at >= start_date,
            OrderModel.processed_at <= end_date
        )
    )
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # Aggregate discount code data
    discount_code_map = {}
    
    for order in orders:
        # Extract discount applications from JSONB field
        discount_applications = order.discount_applications
        
        # Skip orders without discount applications
        if not discount_applications:
            continue
            
        if not isinstance(discount_applications, list):
            continue
            
        # Skip empty discount applications lists
        if len(discount_applications) == 0:
            continue
                
        for discount in discount_applications:
            # Handle both discount_code type and manual discounts with code
            discount_type = discount.get('type')
            code = discount.get('code')
            
            # Handle discounts without a code
            if code is None or code == '':
                # For manual discounts, use the title as the code if available
                if discount_type == 'manual' and 'title' in discount:
                    code = f"MANUAL: {discount.get('title')}"
                # For automatic discounts, use the title or type
                elif discount_type == 'automatic' and 'title' in discount:
                    code = f"AUTO: {discount.get('title')}"
                # For any discount with a title but no code
                elif 'title' in discount and discount.get('title'):
                    code = f"{discount_type.upper() if discount_type else 'DISCOUNT'}: {discount.get('title')}"
                # For discounts with no identifying information
                else:
                    continue
                        
            # Handle different possible discount amount formats
            discount_amount = Decimal('0')
            try:
                if 'amount' in discount:
                    discount_amount = Decimal(str(discount.get('amount', '0')))
                elif 'value' in discount:
                    discount_amount = Decimal(str(discount.get('value', '0')))
                # Some Shopify discounts provide percentage instead of fixed amount
                elif 'percentage' in discount:
                    # Calculate the discount amount based on percentage and order total
                    percentage = Decimal(str(discount.get('percentage', '0'))) / Decimal('100')
                    discount_amount = order.total_price * percentage
                elif 'value_type' in discount and discount.get('value_type') == 'percentage' and 'value' in discount:
                    # Alternative percentage format
                    percentage = Decimal(str(discount.get('value', '0'))) / Decimal('100')
                    discount_amount = order.total_price * percentage
            except (ValueError, TypeError, InvalidOperation) as e:
                discount_amount = Decimal('0')
            
            # Initialize or update discount code stats
            if code not in discount_code_map:
                discount_code_map[code] = {
                    'usage_count': 0,
                    'total_discount_amount': Decimal('0'),
                    'total_sales_generated': Decimal('0')
                }
            
            # Update stats
            discount_code_map[code]['usage_count'] += 1
            discount_code_map[code]['total_discount_amount'] += discount_amount
            discount_code_map[code]['total_sales_generated'] += order.total_price
    
    # Convert to DiscountCodeAnalytics objects
    discount_codes = [
        DiscountCodeAnalytics(
            code=code,
            usage_count=stats['usage_count'],
            total_discount_amount=stats['total_discount_amount'],
            total_sales_generated=stats['total_sales_generated']
        ) for code, stats in discount_code_map.items()
    ]
    
    # Sort by usage count (descending) and limit results
    discount_codes.sort(key=lambda x: x.usage_count, reverse=True)
    
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
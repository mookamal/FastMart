from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import func, select, and_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from strawberry.types import Info

from app.db.models.customer import Customer as CustomerModel
from app.db.models.order import Order as OrderModel
from app.api.graphql.customers.types import Customer
from app.api.graphql.customers.connection import CustomerConnection, CustomerEdge, PageInfo
from app.api.graphql.types.scalars import DateTime, Numeric

async def resolve_customers(info: Info, store_id: str, limit: int = 20, offset: int = 0, 
                          sort_by: Optional[str] = None, sort_desc: bool = False, 
                          search: Optional[str] = None) -> CustomerConnection:
    """Resolver for the customers query that returns paginated customers with analytics data."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    store_uuid = UUID(store_id)
    
    # Start building the query
    query = select(CustomerModel).where(CustomerModel.store_id == store_uuid)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            CustomerModel.email.ilike(search_term) | 
            CustomerModel.first_name.ilike(search_term) | 
            CustomerModel.last_name.ilike(search_term)
        )
    
    # Apply sorting
    if sort_by:
        sort_column = getattr(CustomerModel, sort_by, CustomerModel.synced_at)
        if sort_desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
    else:
        # Default sorting by synced_at desc
        query = query.order_by(desc(CustomerModel.synced_at))
    
    # Get total count for pagination info
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query) or 0
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    customers = result.scalars().all()
    
    # Convert to GraphQL types and create edges
    edges = []
    for customer in customers:
        customer_obj = Customer(
            id=str(customer.id),
            platform_customer_id=customer.platform_customer_id,
            email=customer.email,
            first_name=customer.first_name,
            last_name=customer.last_name,
            orders_count=customer.orders_count,
            total_spent=customer.total_spent,
            platform_created_at=customer.platform_created_at,
            platform_updated_at=customer.platform_updated_at,
            synced_at=customer.synced_at
        )
        edges.append(CustomerEdge(node=customer_obj, cursor=str(customer.id)))
    
    # Create page info
    has_next_page = offset + limit < total_count
    has_previous_page = offset > 0
    start_cursor = edges[0].cursor if edges else None
    end_cursor = edges[-1].cursor if edges else None
    page_info = PageInfo(
        has_next_page=has_next_page,
        has_previous_page=has_previous_page,
        start_cursor=start_cursor,
        end_cursor=end_cursor
    )
    
    return CustomerConnection(
        edges=edges,
        total_count=total_count,
        page_info=page_info
    )

async def resolve_customer_last_order_date(customer_id: str, info: Info) -> Optional[DateTime]:
    """Resolver for the dateOfLastOrder field on the Customer type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    customer_uuid = UUID(customer_id)
    
    # Query for the most recent order
    query = select(OrderModel.processed_at).where(
        OrderModel.customer_id == customer_uuid
    ).order_by(desc(OrderModel.processed_at)).limit(1)
    
    result = await db.execute(query)
    last_order_date = result.scalar()
    
    return last_order_date

async def resolve_customer_lifetime_value(customer_id: str, info: Info) -> Numeric:
    """Resolver for the lifetimeValue field on the Customer type.
    
    For this implementation, we'll use a simple LTV calculation based on total spent,
    but this could be enhanced with more sophisticated calculations in the future.
    """
    context = info.context
    db: AsyncSession = context["db"]
    
    # Convert string ID to UUID
    customer_uuid = UUID(customer_id)
    
    # Query for the customer's total spent
    query = select(CustomerModel.total_spent).where(CustomerModel.id == customer_uuid)
    result = await db.execute(query)
    total_spent = result.scalar() or 0
    
    # For now, LTV is simply the total spent
    # This could be enhanced with more complex calculations in the future
    return total_spent

async def resolve_customer_tags(customer_id: str, info: Info) -> Optional[List[str]]:
    """Resolver for the tags field on the Customer type.
    
    This is a placeholder implementation. In a real application, you would
    query a customer_tags table or similar to get the tags for a customer.
    """
    # This is a placeholder - in a real implementation, you would query the database
    # for tags associated with this customer
    return None
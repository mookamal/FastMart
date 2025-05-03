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
from app.api.graphql.resolvers import BaseResolver
from app.api.graphql.common.connection import encode_cursor, decode_cursor

class CustomerResolver(BaseResolver[CustomerModel, Customer]):
    """Resolver for Customer-related operations."""
    
    model_class = CustomerModel
    graphql_type_class = Customer
    
    @classmethod
    def to_graphql_type(cls, model: CustomerModel) -> Customer:
        """Convert a CustomerModel to a GraphQL Customer type."""
        return Customer(
            id=str(model.id),
            platform_customer_id=model.platform_customer_id,
            email=model.email,
            first_name=model.first_name,
            last_name=model.last_name,
            orders_count=model.orders_count,
            total_spent=model.total_spent,
            platform_created_at=model.platform_created_at,
            platform_updated_at=model.platform_updated_at,
            synced_at=model.synced_at
        )
    
    @classmethod
    async def get_customer_last_order_date(cls, customer_id: str,info: Info) -> Optional[DateTime]:
        """Get the date of the customer's last order."""
        try:
            db: AsyncSession = cls.get_db_from_info(info)
            # Convert string ID to UUID
            customer_uuid = UUID(customer_id)
            
            # Query for the most recent order
            query = select(OrderModel.processed_at).where(
                OrderModel.customer_id == customer_uuid
            ).order_by(desc(OrderModel.processed_at)).limit(1)
            
            result = await db.execute(query)
            last_order_date = result.scalar()
            
            return last_order_date
        except Exception as e:
            raise ValueError(f"Error retrieving customer's last order date: {str(e)}")
    
    @classmethod
    async def get_customer_lifetime_value(cls, customer_id: str, db: AsyncSession) -> Numeric:
        """Get the customer's lifetime value.
        
        For this implementation, we'll use a simple LTV calculation based on total spent,
        but this could be enhanced with more sophisticated calculations in the future.
        """
        try:
            # Convert string ID to UUID
            customer_uuid = UUID(customer_id)
            
            # Query for the customer's total spent
            query = select(cls.model_class.total_spent).where(cls.model_class.id == customer_uuid)
            result = await db.execute(query)
            total_spent = result.scalar() or 0
            
            # For now, LTV is simply the total spent
            # This could be enhanced with more complex calculations in the future
            return total_spent
        except Exception as e:
            raise ValueError(f"Error retrieving customer's lifetime value: {str(e)}")
    
    @classmethod
    async def get_customer_tags(cls, customer_id: str, db: AsyncSession) -> Optional[List[str]]:
        """Get the customer's tags.
        
        This is a placeholder implementation. In a real application, you would
        query a customer_tags table or similar to get the tags for a customer.
        """
        # This is a placeholder - in a real implementation, you would query the database
        # for tags associated with this customer
        return None
    
    @classmethod
    async def get_customers_connection(cls, store_id: str, first: int, after: Optional[str], db: AsyncSession) -> CustomerConnection:
        """Get a paginated connection of customers."""
        try:
            store_uuid = UUID(store_id)
            query = select(cls.model_class).where(cls.model_class.store_id == store_uuid)

            # Apply cursor-based pagination
            if after:
                cursor_value = decode_cursor(after)
                # Assuming cursor is the customer ID
                query = query.where(cls.model_class.id > UUID(cursor_value))

            # Apply limit
            query = query.limit(first + 1)  # +1 to check if there's a next page

            result = await db.execute(query)
            customers = result.scalars().all()

            # Check if there's a next page
            has_next_page = len(customers) > first
            if has_next_page:
                customers = customers[:first]  # Remove the extra item

            # Create edges
            edges = []
            for customer in customers:
                customer = cls.to_graphql_type(customer)
                cursor = encode_cursor(str(customer.id))
                edges.append(CustomerEdge(node=customer, cursor=cursor))

            # Create page info
            start_cursor = edges[0].cursor if edges else None
            end_cursor = edges[-1].cursor if edges else None
            page_info = PageInfo(
                start_cursor=start_cursor,
                end_cursor=end_cursor,
                has_next_page=has_next_page,
                has_previous_page=after is not None
            )
            # Get total count
            total_count_query = select(func.count()).select_from(cls.model_class).where(cls.model_class.store_id == store_uuid)
            total_count_result = await db.execute(total_count_query)
            total_count = total_count_result.scalar()

            return CustomerConnection(
                edges=edges,
                page_info=page_info,
                total_count=total_count
            )


        except Exception as e:
            raise ValueError(f"Error retrieving customers: {str(e)}")




async def resolve_customer_last_order_date(customer_id: str, info: Info) -> Optional[DateTime]:
    """Resolver for the dateOfLastOrder field on the Customer type."""
    context = info.context
    db: AsyncSession = context["db"]
    return await CustomerResolver.get_customer_last_order_date(customer_id, db)

async def resolve_customer_lifetime_value(customer_id: str, info: Info) -> Numeric:
    """Resolver for the lifetimeValue field on the Customer type."""
    context = info.context
    db: AsyncSession = context["db"]
    return await CustomerResolver.get_customer_lifetime_value(customer_id, db)

async def resolve_customer_tags(customer_id: str, info: Info) -> Optional[List[str]]:
    """Resolver for the tags field on the Customer type."""
    context = info.context
    db: AsyncSession = context["db"]
    return await CustomerResolver.get_customer_tags(customer_id, db)
from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info
from app.api.graphql.customers.types import CustomerLtvMetrics
from app.db.models.customer import Customer as CustomerModel
from app.db.models.order import Order as OrderModel
from app.api.graphql.customers.types import Customer
from app.api.graphql.customers.connection import CustomerConnection, CustomerEdge, PageInfo
from app.api.graphql.types.scalars import DateTime, Numeric
from app.api.graphql.resolvers import BaseResolver
from app.api.graphql.common.connection import encode_cursor, decode_cursor
from app.services.analytics.profit_calculator import ProfitCalculator

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
    async def get_customer_lifetime_value(cls, customer_id: str,info: Info) -> Numeric:
        """Get the customer's lifetime value.
        
        For this implementation, we'll use a simple LTV calculation based on total spent,
        but this could be enhanced with more sophisticated calculations in the future.
        """
        try:
            db: AsyncSession = cls.get_db_from_info(info)
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
    async def get_customer_tags(cls, customer_id: str,info:Info) -> Optional[List[str]]:
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

    @classmethod
    async def get_customer_ltv(cls,info: Info, customer_id: str, store_id: str) -> CustomerLtvMetrics:
        """Resolver for customer lifetime value metrics.
        
        Args:
            info: GraphQL resolver info
            customer_id: Customer ID
            store_id: Store ID
            
        Returns:
            CustomerLtvMetrics object containing LTV data
        """
        db: AsyncSession = cls.get_db_from_info(info)
        
        # Convert IDs to UUID
        customer_uuid = UUID(customer_id)
        store_uuid = UUID(store_id)
        
        # Query to get all orders for this customer
        from app.db.models.order import Order
        
        # Get all orders for this customer
        query = select(Order).where(
            and_(
                Order.store_id == store_uuid,
                Order.customer_id == customer_uuid
            )
        ).order_by(Order.processed_at)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        if not orders:
            # Return default values if no orders found
            return CustomerLtvMetrics(
                customer_id=customer_id,
                total_orders=0,
                total_revenue=0,
                total_profit=0,
                net_profit_ltv=0,
                average_order_value=0,
                average_profit_per_order=0,
                first_order_date=None,
                last_order_date=None
            )
        
        # Calculate metrics
        total_orders = len(orders)
        total_revenue = sum(order.total_price for order in orders)
        
        # Calculate profit for each order
        total_profit = 0
        for order in orders:
            # Get order date range
            order_date = order.processed_at
            # Calculate profit for this order
            profit_data = await ProfitCalculator.calculate_net_profit(
                db=db,
                store_id=store_id,
                start_date=order_date,
                end_date=order_date
            )
            total_profit += profit_data["net_profit"]
        
        # Calculate averages
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        average_profit_per_order = total_profit / total_orders if total_orders > 0 else 0
        
        # Get first and last order dates
        first_order_date = orders[0].processed_at.date()
        last_order_date = orders[-1].processed_at.date()
        
        # Return customer LTV metrics
        return CustomerLtvMetrics(
            customer_id=customer_id,
            total_orders=total_orders,
            total_revenue=total_revenue,
            total_profit=total_profit,
            net_profit_ltv=total_profit,  # Net profit LTV is the total profit from all orders
            average_order_value=average_order_value,
            average_profit_per_order=average_profit_per_order,
            first_order_date=first_order_date,
            last_order_date=last_order_date
        )
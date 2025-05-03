from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.db.models.line_item import LineItem
from app.db.models.product_variant import ProductVariant
from app.db.models.ad_spend import AdSpend
from app.db.models.other_cost import OtherCost
from app.db.models.transaction_fee_rule import TransactionFeeRule
from app.db.models.shipping_cost_rule import ShippingCostRule


class ProfitCalculator:
    """Service for calculating profit metrics including Net Profit."""

    @staticmethod
    async def calculate_net_profit(
        db: AsyncSession,
        store_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Decimal]:
        """Calculate net profit for a store within a date range.
        
        Args:
            db: Database session
            store_id: Store ID
            start_date: Start date for the calculation period
            end_date: End date for the calculation period
            
        Returns:
            Dictionary containing profit metrics:
            - gross_revenue: Sum of all order totals
            - net_revenue: Gross revenue minus refunds and discounts
            - gross_profit: Net revenue minus COGS
            - net_profit: Gross profit minus shipping, transaction fees, ad spend, and other costs
            - total_cogs: Total cost of goods sold
            - total_shipping_cost: Total actual shipping costs
            - total_transaction_fees: Total transaction fees
            - total_ad_spend: Total ad spend within the period
            - total_other_costs: Total other costs within the period
            - total_refunds: Total refund amount
            - total_discounts: Total discount amount
        """
        store_uuid = UUID(store_id)
        
        # Fetch orders within the date range
        orders_data = await ProfitCalculator._fetch_orders(db, store_uuid, start_date, end_date)
        
        # Calculate revenue metrics
        gross_revenue = orders_data["gross_revenue"]
        total_refunds = Decimal('0')  # Placeholder for refunds calculation
        total_discounts = orders_data["total_discounts"]
        
        # Calculate net revenue
        net_revenue = gross_revenue - total_refunds - total_discounts
        
        # Calculate COGS
        total_cogs = await ProfitCalculator._calculate_total_cogs(db, store_uuid, start_date, end_date)
        
        # Calculate gross profit
        gross_profit = net_revenue - total_cogs
        
        # Calculate shipping costs
        total_shipping_cost = await ProfitCalculator._calculate_shipping_costs(db, store_uuid, start_date, end_date)
        
        # Calculate transaction fees
        total_transaction_fees = await ProfitCalculator._calculate_transaction_fees(db, store_uuid, start_date, end_date)
        
        # Calculate ad spend
        total_ad_spend = await ProfitCalculator._calculate_ad_spend(db, store_uuid, start_date, end_date)
        
        # Calculate other costs
        total_other_costs = await ProfitCalculator._calculate_other_costs(db, store_uuid, start_date, end_date)
        
        # Calculate net profit
        net_profit = gross_profit - total_shipping_cost - total_transaction_fees - total_ad_spend - total_other_costs
        
        return {
            "gross_revenue": gross_revenue,
            "net_revenue": net_revenue,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "total_cogs": total_cogs,
            "total_shipping_cost": total_shipping_cost,
            "total_transaction_fees": total_transaction_fees,
            "total_ad_spend": total_ad_spend,
            "total_other_costs": total_other_costs,
            "total_refunds": total_refunds,
            "total_discounts": total_discounts
        }
    
    @staticmethod
    async def _fetch_orders(
        db: AsyncSession,
        store_uuid: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Decimal]:
        """Fetch orders and calculate revenue and discount totals."""
        # Query for total revenue and discounts
        query = select(
            func.sum(Order.total_price).label("gross_revenue"),
            func.sum(func.coalesce(func.jsonb_array_length(Order.discount_applications), 0)).label("discount_count")
        ).where(
            and_(
                Order.store_id == store_uuid,
                Order.processed_at >= start_date,
                Order.processed_at <= end_date
            )
        )
        
        result = await db.execute(query)
        data = result.fetchone()
        
        gross_revenue = data.gross_revenue or Decimal('0')
        
        # Calculate total discounts by examining discount_applications in each order
        total_discounts = await ProfitCalculator._calculate_total_discounts(db, store_uuid, start_date, end_date)
        
        return {
            "gross_revenue": gross_revenue,
            "total_discounts": total_discounts
        }
    
    @staticmethod
    async def _calculate_total_discounts(
        db: AsyncSession,
        store_uuid: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Decimal:
        """Calculate total discounts from order discount_applications."""
        # Fetch orders with discount applications
        query = select(Order).where(
            and_(
                Order.store_id == store_uuid,
                Order.processed_at >= start_date,
                Order.processed_at <= end_date,
                Order.discount_applications.is_not(None)
            )
        )
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        total_discounts = Decimal('0')
        
        for order in orders:
            discount_applications = order.discount_applications
            if not discount_applications or not isinstance(discount_applications, list):
                continue
                
            for discount in discount_applications:
                discount_amount = Decimal('0')
                try:
                    if 'amount' in discount:
                        discount_amount = Decimal(str(discount.get('amount', '0')))
                    elif 'value' in discount:
                        discount_amount = Decimal(str(discount.get('value', '0')))
                    elif 'percentage' in discount:
                        percentage = Decimal(str(discount.get('percentage', '0'))) / Decimal('100')
                        discount_amount = order.total_price * percentage
                    elif 'value_type' in discount and discount.get('value_type') == 'percentage' and 'value' in discount:
                        percentage = Decimal(str(discount.get('value', '0'))) / Decimal('100')
                        discount_amount = order.total_price * percentage
                except (ValueError, TypeError) as e:
                    discount_amount = Decimal('0')
                    
                total_discounts += discount_amount
        
        return total_discounts
    
    @staticmethod
    async def _calculate_total_cogs(
        db: AsyncSession,
        store_uuid: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Decimal:
        """Calculate total COGS for all line items in the date range."""
        # Join LineItem with Order and ProductVariant to get COGS
        query = select(
            func.sum(LineItem.quantity * func.coalesce(ProductVariant.cost_of_goods_sold, 0))
        ).select_from(
            LineItem
        ).join(
            Order, LineItem.order_id == Order.id
        ).join(
            ProductVariant, 
            and_(
                LineItem.platform_variant_id == ProductVariant.platform_variant_id,
                LineItem.product_id == ProductVariant.product_id
            ),
            isouter=True
        ).where(
            and_(
                Order.store_id == store_uuid,
                Order.processed_at >= start_date,
                Order.processed_at <= end_date
            )
        )
        
        result = await db.execute(query)
        total_cogs = result.scalar() or Decimal('0')
        
        return total_cogs
    
    @staticmethod
    async def _calculate_shipping_costs(
        db: AsyncSession,
        store_uuid: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Decimal:
        """Calculate total shipping costs for orders in the date range."""
        # Query for orders with actual_shipping_cost
        query = select(
            func.sum(func.coalesce(Order.actual_shipping_cost, 0))
        ).where(
            and_(
                Order.store_id == store_uuid,
                Order.processed_at >= start_date,
                Order.processed_at <= end_date
            )
        )
        
        result = await db.execute(query)
        total_shipping_cost = result.scalar() or Decimal('0')
        
        return total_shipping_cost
    
    @staticmethod
    async def _calculate_transaction_fees(
        db: AsyncSession,
        store_uuid: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Decimal:
        """Calculate transaction fees for orders in the date range.
        
        This is a placeholder implementation. In a real application, you would
        apply transaction fee rules to each order based on payment method, etc.
        """
        # For now, we'll use a simple estimate based on total revenue
        query = select(func.sum(Order.total_price)).where(
            and_(
                Order.store_id == store_uuid,
                Order.processed_at >= start_date,
                Order.processed_at <= end_date
            )
        )
        
        result = await db.execute(query)
        total_revenue = result.scalar() or Decimal('0')
        
        # Apply a default transaction fee rate (e.g., 2.9% + $0.30 per transaction)
        # This is a simplified calculation and should be replaced with actual fee rules
        query_count = select(func.count(Order.id)).where(
            and_(
                Order.store_id == store_uuid,
                Order.processed_at >= start_date,
                Order.processed_at <= end_date
            )
        )
        
        result = await db.execute(query_count)
        order_count = result.scalar() or 0
        
        # Default transaction fee calculation (placeholder)
        transaction_fee_rate = Decimal('0.029')  # 2.9%
        transaction_fee_fixed = Decimal('0.30')  # $0.30 per transaction
        
        total_transaction_fees = (total_revenue * transaction_fee_rate) + (transaction_fee_fixed * order_count)
        
        return total_transaction_fees
    
    @staticmethod
    async def _calculate_ad_spend(
        db: AsyncSession,
        store_uuid: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Decimal:
        """Calculate total ad spend within the date range."""
        query = select(func.sum(AdSpend.spend)).where(
            and_(
                AdSpend.store_id == store_uuid,
                AdSpend.date >= start_date.date(),
                AdSpend.date <= end_date.date()
            )
        )
        
        result = await db.execute(query)
        total_ad_spend = result.scalar() or Decimal('0')
        
        return total_ad_spend
    
    @staticmethod
    async def _calculate_other_costs(
        db: AsyncSession,
        store_uuid: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Decimal:
        """Calculate other costs applicable to the date range."""
        # For one-time costs that fall within the date range
        query_one_time = select(func.sum(OtherCost.amount)).where(
            and_(
                OtherCost.store_id == store_uuid,
                OtherCost.frequency == 'one_time',
                OtherCost.start_date >= start_date.date(),
                OtherCost.start_date <= end_date.date()
            )
        )
        
        # For recurring costs that overlap with the date range
        query_recurring = select(func.sum(OtherCost.amount)).where(
            and_(
                OtherCost.store_id == store_uuid,
                OtherCost.frequency != 'one_time',
                OtherCost.start_date <= end_date.date(),
                or_(
                    OtherCost.end_date.is_(None),
                    OtherCost.end_date >= start_date.date()
                )
            )
        )
        
        result_one_time = await db.execute(query_one_time)
        result_recurring = await db.execute(query_recurring)
        
        one_time_costs = result_one_time.scalar() or Decimal('0')
        recurring_costs = result_recurring.scalar() or Decimal('0')
        
        # For recurring costs, we need to prorate based on the date range
        # This is a simplified implementation and should be enhanced for real-world use
        
        return one_time_costs + recurring_costs
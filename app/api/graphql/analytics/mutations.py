import strawberry
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.types import Info

from app.db.models.product_variant import ProductVariant as ProductVariantModel
from app.db.models.order import Order as OrderModel
from app.db.models.ad_spend import AdSpend as AdSpendModel
from app.db.models.other_cost import OtherCost as OtherCostModel
from app.api.graphql.types.scalars import Numeric, Date
from app.api.graphql.analytics.types import (
    ProductVariantCogsInput, 
    AdSpendInput, 
    OtherCostInput,
    ShippingCostRuleInput,
    TransactionFeeRuleInput,
    ProductVariant,
    AdSpend,
    OtherCost
)

@strawberry.type
class AnalyticsMutation:
    @strawberry.mutation
    async def update_product_variant_cogs(
        self, 
        info: Info, 
        variant_id: strawberry.ID, 
        cogs: Numeric
    ) -> ProductVariant:
        """Update the cost of goods sold for a product variant."""
        db: AsyncSession = info.context["db"]
        
        # Convert string ID to UUID
        variant_uuid = UUID(variant_id)
        
        # Update the product variant
        stmt = update(ProductVariantModel).where(
            ProductVariantModel.id == variant_uuid
        ).values(cost_of_goods_sold=cogs).returning(ProductVariantModel)
        
        result = await db.execute(stmt)
        await db.commit()
        
        updated_variant = result.scalar_one()
        
        return ProductVariant(
            id=str(updated_variant.id),
            title=updated_variant.title,
            sku=updated_variant.sku,
            cost_of_goods_sold=updated_variant.cost_of_goods_sold
        )
    
    @strawberry.mutation
    async def bulk_update_cogs(
        self, 
        info: Info, 
        inputs: List[ProductVariantCogsInput]
    ) -> List[ProductVariant]:
        """Bulk update cost of goods sold for multiple product variants."""
        db: AsyncSession = info.context["db"]
        updated_variants = []
        
        for input_item in inputs:
            variant_uuid = UUID(input_item.variant_id)
            
            stmt = update(ProductVariantModel).where(
                ProductVariantModel.id == variant_uuid
            ).values(cost_of_goods_sold=input_item.cogs).returning(ProductVariantModel)
            
            result = await db.execute(stmt)
            updated_variant = result.scalar_one()
            
            updated_variants.append(ProductVariant(
                id=str(updated_variant.id),
                title=updated_variant.title,
                sku=updated_variant.sku,
                cost_of_goods_sold=updated_variant.cost_of_goods_sold
            ))
        
        await db.commit()
        return updated_variants
    
    @strawberry.mutation
    async def update_order_shipping_cost(
        self, 
        info: Info, 
        order_id: strawberry.ID, 
        cost: Numeric
    ) -> bool:
        """Update the actual shipping cost for an order."""
        db: AsyncSession = info.context["db"]
        
        # Convert string ID to UUID
        order_uuid = UUID(order_id)
        
        # Update the order
        stmt = update(OrderModel).where(
            OrderModel.id == order_uuid
        ).values(actual_shipping_cost=cost)
        
        await db.execute(stmt)
        await db.commit()
        
        return True
    
    @strawberry.mutation
    async def add_ad_spend(
        self, 
        info: Info, 
        inputs: List[AdSpendInput]
    ) -> List[AdSpend]:
        """Add ad spend records."""
        db: AsyncSession = info.context["db"]
        added_records = []
        
        for input_item in inputs:
            store_uuid = UUID(input_item.store_id)
            
            # Create new ad spend record
            new_ad_spend = AdSpendModel(
                store_id=store_uuid,
                platform=input_item.platform,
                date=input_item.date,
                spend=input_item.spend,
                campaign_name=input_item.campaign_name
            )
            
            db.add(new_ad_spend)
            await db.flush()
            
            added_records.append(AdSpend(
                id=str(new_ad_spend.id),
                platform=new_ad_spend.platform,
                date=new_ad_spend.date,
                spend=new_ad_spend.spend,
                campaign_name=new_ad_spend.campaign_name
            ))
        
        await db.commit()
        return added_records
    
    @strawberry.mutation
    async def add_other_cost(
        self, 
        info: Info, 
        input: OtherCostInput
    ) -> OtherCost:
        """Add an other cost record."""
        db: AsyncSession = info.context["db"]
        store_uuid = UUID(input.store_id)
        
        # Create new other cost record
        new_other_cost = OtherCostModel(
            store_id=store_uuid,
            category=input.category,
            description=input.description,
            amount=input.amount,
            start_date=input.start_date,
            end_date=input.end_date,
            frequency=input.frequency
        )
        
        db.add(new_other_cost)
        await db.commit()
        
        return OtherCost(
            id=str(new_other_cost.id),
            category=new_other_cost.category,
            description=new_other_cost.description,
            amount=new_other_cost.amount,
            start_date=new_other_cost.start_date,
            end_date=new_other_cost.end_date,
            frequency=new_other_cost.frequency
        )
    
    @strawberry.mutation
    async def update_other_cost(
        self, 
        info: Info, 
        id: strawberry.ID, 
        input: OtherCostInput
    ) -> OtherCost:
        """Update an other cost record."""
        db: AsyncSession = info.context["db"]
        cost_uuid = UUID(id)
        store_uuid = UUID(input.store_id)
        
        # Update the other cost record
        stmt = update(OtherCostModel).where(
            OtherCostModel.id == cost_uuid
        ).values(
            store_id=store_uuid,
            category=input.category,
            description=input.description,
            amount=input.amount,
            start_date=input.start_date,
            end_date=input.end_date,
            frequency=input.frequency
        ).returning(OtherCostModel)
        
        result = await db.execute(stmt)
        await db.commit()
        
        updated_cost = result.scalar_one()
        
        return OtherCost(
            id=str(updated_cost.id),
            category=updated_cost.category,
            description=updated_cost.description,
            amount=updated_cost.amount,
            start_date=updated_cost.start_date,
            end_date=updated_cost.end_date,
            frequency=updated_cost.frequency
        )
    
    @strawberry.mutation
    async def delete_other_cost(
        self, 
        info: Info, 
        id: strawberry.ID
    ) -> bool:
        """Delete an other cost record."""
        db: AsyncSession = info.context["db"]
        cost_uuid = UUID(id)
        
        # Delete the other cost record
        stmt = select(OtherCostModel).where(OtherCostModel.id == cost_uuid)
        result = await db.execute(stmt)
        cost = result.scalar_one_or_none()
        
        if cost:
            await db.delete(cost)
            await db.commit()
            return True
        
        return False
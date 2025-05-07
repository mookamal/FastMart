from typing import List
from uuid import UUID

from strawberry.types import Info
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

from app.db.models.store import Store as StoreModel
from app.db.models.product import Product as ProductModel
from app.db.models.customer import Customer as CustomerModel
from app.db.models.order import Order as OrderModel
from app.api.graphql.products.types import Product
from app.api.graphql.customers.types import Customer
from app.api.graphql.orders.types import Order
from app.api.graphql.stores.types import Store
from app.core.auth import get_current_user

async def resolve_store(info: Info, id: str) -> Store:
    """Resolver for the store query that returns a specific store by ID."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Query the database for the store
    # Note: Permission check is now handled by StoreOwnerPermission class
    store_model = await db.get(StoreModel, UUID(id))
    if not store_model:
        raise ValueError("Store not found")
    
    # Convert the model to a GraphQL type
    return Store(
        id=str(store_model.id),
        platform=store_model.platform,
        shop_domain=store_model.shop_domain,
        is_active=store_model.is_active,
        last_sync_at=store_model.last_sync_at,
        created_at=store_model.created_at,
        currency=store_model.currency,
    )

async def resolve_store_products(store: Store, info: Info) -> List[Product]:
    """Resolver for the products field on the Store type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Query the database for the store's products
    stmt = select(ProductModel).where(ProductModel.store_id == UUID(store.id))
    result = await db.execute(stmt)
    product_models = result.scalars().all()
    
    # Convert the models to GraphQL types
    return [
        Product(
            id=str(product.id),
            platform_product_id=product.platform_product_id,
            title=product.title,
            vendor=product.vendor,
            product_type=product.product_type,
            platform_created_at=product.platform_created_at,
            platform_updated_at=product.platform_updated_at,
            synced_at=product.synced_at
        ) for product in product_models
    ]

async def resolve_store_customers(store: Store, info: Info) -> List[Customer]:
    """Resolver for the customers field on the Store type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Query the database for the store's customers
    stmt = select(CustomerModel).where(CustomerModel.store_id == UUID(store.id))
    result = await db.execute(stmt)
    customer_models = result.scalars().all()
    
    # Convert the models to GraphQL types
    return [
        Customer(
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
        ) for customer in customer_models
    ]

async def resolve_store_orders(store: Store, info: Info) -> List[Order]:
    """Resolver for the orders field on the Store type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Query the database for the store's orders
    stmt = select(OrderModel).where(OrderModel.store_id == UUID(store.id))
    result = await db.execute(stmt)
    order_models = result.scalars().all()
    
    # Convert the models to GraphQL types
    return [
        Order(
            id=str(order.id),
            platform_order_id=order.platform_order_id,
            order_number=order.order_number,
            total_price=order.total_price,
            currency=order.currency,
            financial_status=order.financial_status,
            fulfillment_status=order.fulfillment_status,
            processed_at=order.processed_at,
            platform_created_at=order.platform_created_at,
            platform_updated_at=order.platform_updated_at,
            synced_at=order.synced_at
        ) for order in order_models
    ]
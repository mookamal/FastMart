from uuid import UUID
from datetime import datetime, timedelta
import logging
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Customer, Order, Product, Store
from app.services.platform_connector import get_connector
from app.tasks.async_helper import celery_async_task
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Helper functions
async def get_customer_by_platform_id(db: AsyncSession, store_id: int, platform_customer_id: str) -> Customer | None:
    result = await db.execute(
        select(Customer).where(Customer.store_id == store_id, Customer.platform_customer_id == platform_customer_id)
    )
    return result.scalars().first()

async def upsert_customer(db: AsyncSession, customer_data: dict):
    # Extract tags from customer_data if present
    tags = customer_data.pop('tags', None)
    
    stmt = insert(Customer).values(**customer_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Customer.store_id, Customer.platform_customer_id],
        set_=customer_data
    )
    await db.execute(stmt)
    # Fetch the inserted/updated customer to get the ID
    return await get_customer_by_platform_id(db, customer_data['store_id'], customer_data['platform_customer_id'])

async def upsert_product(db: AsyncSession, product_data: dict):
    # Extract inventory_levels from product_data if present
    inventory_levels = product_data.pop('inventory_levels', None)
    
    stmt = insert(Product).values(**product_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Product.store_id, Product.platform_product_id],
        set_=product_data
    )
    await db.execute(stmt)

async def upsert_order(db: AsyncSession, order_data: dict):
    # Extract line_items and discount_applications from order_data
    line_items = order_data.pop('line_items', [])
    discount_applications = order_data.pop('discount_applications', None)
    
    stmt = insert(Order).values(**order_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Order.store_id, Order.platform_order_id],
        set_=order_data
    )
    await db.execute(stmt)
    
    # Process line items (existing logic)
    # ...

@celery_async_task()
async def sync_store(self, store_id: UUID):
    """Celery task to perform initial data synchronization for a store."""
    logger.info(f"Starting initial sync for store_id: {store_id}")
    # Implementation remains the same, but will use updated connector methods
    # that fetch additional data for analytics
    
@celery_async_task()
async def periodic_sync_store(self, store_id: UUID):
    """Task for periodically syncing data for a specific store."""
    # Implementation remains the same, but will use updated connector methods
    # that fetch additional data for analytics

# Proposed updates to the ShopifyConnector class:
"""
Updates needed in ShopifyConnector class:

1. Update map_customer_to_db_model to include tags:
   ```python
   async def map_customer_to_db_model(self, platform_customer_data: Dict) -> Dict:
       return {
           # Existing fields...
           'tags': platform_customer_data.get('tags', '').split(',') if platform_customer_data.get('tags') else [],
       }
   ```

2. Update map_order_to_db_model to include discount applications:
   ```python
   async def map_order_to_db_model(self, platform_order_data: Dict) -> Dict:
       return {
           # Existing fields...
           'discount_applications': platform_order_data.get('discount_applications', []),
       }
   ```

3. Add a new method to fetch inventory levels:
   ```python
   async def fetch_inventory_levels(self, access_token: str, shop_domain: str) -> List[Dict]:
       client = await self.get_api_client(access_token, shop_domain)
       try:
           inventory_levels = await self._fetch_all_resources(
               client.InventoryLevel,
               limit=250
           )
           return inventory_levels
       except Exception as e:
           print(f"Error fetching Shopify inventory levels for {shop_domain}: {e}")
           raise e
       finally:
           client.ShopifyResource.clear_session()
   ```

4. Update the sync_store_logic method to fetch and process inventory levels:
   ```python
   # After processing products
   logger.info(f"Fetching inventory levels for store {store_id}...")
   inventory_levels = await connector.fetch_inventory_levels(access_token=store.access_token, shop_domain=store.shop_domain)
   
   # Create a mapping of inventory_item_id to inventory level
   inventory_map = {}
   for level in inventory_levels:
       inventory_map[level.get('inventory_item_id')] = {
           'available': level.get('available'),
           'location_id': level.get('location_id')
       }
   
   # Update products with inventory levels
   # This would require fetching product variants to get inventory_item_ids
   ```
"""
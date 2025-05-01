import logging
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from app.tasks.celery_app import celery_app
from app.db.models import Store, Product, Customer, Order, LineItem
from app.services.platform_connector import get_connector
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.base import AsyncSessionLocal
from app.tasks.async_helper import celery_async_task
logger = logging.getLogger(__name__) 

# --- Placeholder CRUD Functions (Replace with actual CRUD module imports if they exist) ---

async def get_customer_by_platform_id(db: AsyncSession, store_id: int, platform_customer_id: str) -> Customer | None:
    result = await db.execute(
        select(Customer).where(Customer.store_id == store_id, Customer.platform_customer_id == platform_customer_id)
    )
    return result.scalars().first()

async def get_product_by_platform_id(db: AsyncSession, store_id: int, platform_product_id: str) -> Product | None:
    result = await db.execute(
        select(Product).where(Product.store_id == store_id, Product.platform_product_id == platform_product_id)
    )
    return result.scalars().first()

async def upsert_customer(db: AsyncSession, customer_data: dict):
    stmt = insert(Customer).values(**customer_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Customer.store_id, Customer.platform_customer_id],
        set_=customer_data
    )
    await db.execute(stmt)
    # Fetch the inserted/updated customer to get the ID
    return await get_customer_by_platform_id(db, customer_data['store_id'], customer_data['platform_customer_id'])

async def upsert_product(db: AsyncSession, product_data: dict):
    stmt = insert(Product).values(**product_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Product.store_id, Product.platform_product_id],
        set_=product_data
    )
    await db.execute(stmt)
    return await get_product_by_platform_id(db, product_data['store_id'], product_data['platform_product_id'])

async def upsert_order(db: AsyncSession, order_data: dict):
    # Ensure line_items are removed before upserting the order itself
    line_items_data = order_data.pop('line_items', [])
    
    stmt = insert(Order).values(**order_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Order.store_id, Order.platform_order_id],
        set_=order_data
    ).returning(Order.id)
    result = await db.execute(stmt)
    order_id = result.scalar_one()
    
    # Handle line items after order is upserted
    if order_id and line_items_data:
        # Consider deleting existing line items for this order before inserting new ones
        # Or implement upsert logic for line items as well
        for item_data in line_items_data:
            item_data['order_id'] = order_id
            # Find product_id based on platform_product_id
            product = await get_product_by_platform_id(db, order_data['store_id'], item_data.get('platform_product_id'))
            if product:
                item_data['product_id'] = product.id
            else:
                 # Handle case where product doesn't exist (log, skip, etc.)
                 logger.warning(f"Product with platform ID {item_data.get('platform_product_id')} not found for store {item_data['store_id']}. Skipping line item.")
                 continue
            
            # Upsert line item (assuming platform_line_item_id exists and is unique per order)
            line_item_stmt = insert(LineItem).values(**item_data)
            line_item_stmt = line_item_stmt.on_conflict_do_update(
                index_elements=[LineItem.order_id, LineItem.platform_line_item_id], # Assuming this unique constraint
                set_=item_data
            )
            await db.execute(line_item_stmt)
            
    return order_id # Or potentially the full Order object if needed

# --- Celery Task Definition ---

async def sync_store_logic(self, store_id: UUID,db: AsyncSession):
    """Celery task to perform initial data synchronization for a store."""
    logger.info(f"Starting initial sync for store_id: {store_id}")
    # Ensure db is valid and connected
    if db.is_active:
        logger.info(f"Database session is active for store_id: {store_id}")
    else:
        logger.error(f"Database session is not active for store_id: {store_id}")
        return f"Database session not active for store {store_id}."
        
    try:
        # 1. Fetch Store
        result = await db.execute(select(Store).where(Store.id == store_id))
        store = result.scalars().first()

        if not store:
            logger.error(f"Store with id {store_id} not found.")
            return f"Store {store_id} not found."
        if not store.is_active:
            logger.warning(f"Store {store_id} is not active. Skipping sync.")
            return f"Store {store_id} inactive."

        # 2. Get Connector and Decrypt Token
        connector = get_connector(store.platform)
        if store.platform.lower() != 'shopify': # Basic check
             logger.error(f"Store {store_id} is not a Shopify store. Platform: {store.platform}")
             return f"Store {store_id} is not Shopify."

        # 3. Define Sync Time Range (e.g., last 6 months)
        sync_end_date = datetime.utcnow()
        sync_start_date = sync_end_date - timedelta(days=180) # Approx 6 months

        # 4. Fetch and Process Data
        # --- Products ---
        logger.info(f"Fetching products for store {store_id}...")
        async for products_batch in connector.fetch_products(access_token=store.access_token, shop_domain=store.shop_domain):
            logger.info(f"Processing batch of {len(products_batch)} products...")
            for product_data_raw in products_batch:
                try:
                    product_db_data = await connector.map_product_to_db_model(product_data_raw)
                    product_db_data['store_id'] = store.id
                    await upsert_product(db, product_db_data)
                except Exception as e:
                    logger.error(f"Error processing product {product_data_raw.get('id')} for store {store_id}: {e}", exc_info=True)
            await db.commit() # Commit after each batch

        # --- Customers ---
        logger.info(f"Fetching customers for store {store_id}...")
        async for customers_batch in connector.fetch_customers(access_token=store.access_token, shop_domain=store.shop_domain):
            logger.info(f"Processing batch of {len(customers_batch)} customers...")
            for customer_data_raw in customers_batch:
                try:
                    customer_db_data = await connector.map_customer_to_db_model(customer_data_raw)
                    customer_db_data['store_id'] = store.id
                    await upsert_customer(db, customer_db_data)
                except Exception as e:
                    logger.error(f"Error processing customer {customer_data_raw.get('id')} for store {store_id}: {e}", exc_info=True)
            await db.commit() # Commit after each batch

        # --- Orders ---
        logger.info(f"Fetching orders for store {store_id} from {sync_start_date} to {sync_end_date}...")
        async for orders_batch in connector.fetch_orders(access_token=store.access_token, shop_domain=store.shop_domain, since=sync_start_date): # Pass token, domain, and since
            # Note: Shopify API usually uses 'since_id' or 'updated_at_min' for filtering, not created_at range directly for all resources.
            # Adjusting to use 'since' based on connector's _fetch_all_resources which uses 'updated_at_min'.
            # If created_at filtering is strictly needed, the connector method might need adjustment.
            logger.info(f"Processing batch of {len(orders_batch)} orders...")
            for order_data_raw in orders_batch:
                try:
                    order_db_data = await connector.map_order_to_db_model(order_data_raw)
                    order_db_data['store_id'] = store.id

                    # Find associated customer_id
                    platform_customer_id = order_db_data.pop('platform_customer_id', None) # Get platform ID from mapped data
                    customer = None
                    if platform_customer_id:
                        customer = await get_customer_by_platform_id(db, store.id, platform_customer_id)
                    
                    if customer:
                        order_db_data['customer_id'] = customer.id
                    else:
                        order_db_data['customer_id'] = None # Or handle as needed if customer must exist
                        logger.warning(f"Customer with platform ID {platform_customer_id} not found for store {store_id} while processing order {order_data_raw.get('id')}.")

                    # Extract line items (assuming map_order_to_db_model includes them or they need separate mapping)
                    # The placeholder upsert_order handles line items internally now
                    line_items_raw = order_data_raw.get('line_items', [])
                    mapped_line_items = [
                        await connector.map_line_item_to_db_model(item) for item in line_items_raw
                    ]
                    order_db_data['line_items'] = mapped_line_items # Pass mapped items to upsert

                    await upsert_order(db, order_db_data)
                except Exception as e:
                    logger.error(f"Error processing order {order_data_raw.get('id')} for store {store_id}: {e}", exc_info=True)
            await db.commit() # Commit after each batch

        # 5. Update Last Sync Time
        store.last_sync_at = datetime.utcnow()
        db.add(store)
        await db.commit()
        logger.info(f"Successfully completed initial sync for store_id: {store_id}")
        return f"Sync completed for store {store_id}."

    except Exception as exc:
        logger.error(f"Initial sync failed for store {store_id}: {exc}", exc_info=True)
        await db.rollback() # Rollback on failure
        try:
            # Retry the task with exponential backoff
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.critical(f"Initial sync for store {store_id} failed after max retries.")
            # Optionally, mark the store sync status as failed in the DB
            return f"Sync failed permanently for store {store_id}."
    finally:
        # Ensure the database session is properly closed if it's still active
        if db and db.is_active:
            try:
                await db.close()
                logger.info(f"Database session closed for store_id: {store_id}")
            except Exception as e:
                logger.error(f"Error closing database session for store_id {store_id}: {e}", exc_info=True)

@celery_async_task()
async def initial_sync_store(self, store_id: UUID):
    """Task for initial store synchronization"""
    async with AsyncSessionLocal() as db:
        return await sync_store_logic(self, store_id, db)

async def _periodic_sync_logic(self, store_id: UUID, db: AsyncSession):
    """Logic for periodically syncing data for a specific store.
    
    This function syncs data that has been updated since the last sync.
    It uses the store's last_sync_at timestamp as the starting point.
    """
    logger.info(f"Starting periodic sync for store_id: {store_id}")
    # Ensure db is valid and connected
    if db.is_active:
        logger.info(f"Database session is active for store_id: {store_id}")
    else:
        logger.error(f"Database session is not active for store_id: {store_id}")
        return f"Database session not active for store {store_id}."
        
    try:
        # 1. Fetch Store
        result = await db.execute(select(Store).where(Store.id == store_id))
        store = result.scalars().first()

        if not store:
            logger.error(f"Store with id {store_id} not found.")
            return f"Store {store_id} not found."
        if not store.is_active:
            logger.warning(f"Store {store_id} is not active. Skipping sync.")
            return f"Store {store_id} inactive."

        # 2. Get Connector and Decrypt Token
        connector = get_connector(store.platform)
        if store.platform.lower() != 'shopify': # Basic check
             logger.error(f"Store {store_id} is not a Shopify store. Platform: {store.platform}")
             return f"Store {store_id} is not Shopify."

        # 3. Define Sync Time Range (from last sync to now)
        sync_end_date = datetime.utcnow()
        
        # Use last_sync_at as the starting point, with a small buffer to avoid missing data
        # If last_sync_at is None (never synced), use a default (e.g., 7 days ago)
        if store.last_sync_at:
            # Add a small buffer (e.g., 5 minutes) to avoid missing data due to timing issues
            sync_start_date = store.last_sync_at - timedelta(minutes=5)
        else:
            # If never synced before, use a default timeframe (e.g., last 7 days)
            sync_start_date = sync_end_date - timedelta(days=7)
            logger.warning(f"No previous sync found for store {store_id}. Using default timeframe of 7 days.")

        logger.info(f"Syncing data for store {store_id} from {sync_start_date} to {sync_end_date}")

        # 4. Fetch and Process Data
        # --- Products ---
        logger.info(f"Fetching products updated since {sync_start_date} for store {store_id}...")
        async for products_batch in connector.fetch_products(access_token=store.access_token, 
                                                           shop_domain=store.shop_domain, 
                                                           since=sync_start_date):
            logger.info(f"Processing batch of {len(products_batch)} products...")
            for product_data_raw in products_batch:
                try:
                    product_db_data = await connector.map_product_to_db_model(product_data_raw)
                    product_db_data['store_id'] = store.id
                    await upsert_product(db, product_db_data)
                except Exception as e:
                    logger.error(f"Error processing product {product_data_raw.get('id')} for store {store_id}: {e}", exc_info=True)
            await db.commit() # Commit after each batch

        # --- Customers ---
        logger.info(f"Fetching customers updated since {sync_start_date} for store {store_id}...")
        async for customers_batch in connector.fetch_customers(access_token=store.access_token, 
                                                             shop_domain=store.shop_domain, 
                                                             since=sync_start_date):
            logger.info(f"Processing batch of {len(customers_batch)} customers...")
            for customer_data_raw in customers_batch:
                try:
                    customer_db_data = await connector.map_customer_to_db_model(customer_data_raw)
                    customer_db_data['store_id'] = store.id
                    await upsert_customer(db, customer_db_data)
                except Exception as e:
                    logger.error(f"Error processing customer {customer_data_raw.get('id')} for store {store_id}: {e}", exc_info=True)
            await db.commit() # Commit after each batch

        # --- Orders ---
        logger.info(f"Fetching orders updated since {sync_start_date} for store {store_id}...")
        async for orders_batch in connector.fetch_orders(access_token=store.access_token, 
                                                       shop_domain=store.shop_domain, 
                                                       since=sync_start_date):
            logger.info(f"Processing batch of {len(orders_batch)} orders...")
            for order_data_raw in orders_batch:
                try:
                    order_db_data = await connector.map_order_to_db_model(order_data_raw)
                    order_db_data['store_id'] = store.id

                    # Find associated customer_id
                    platform_customer_id = order_db_data.pop('platform_customer_id', None) # Get platform ID from mapped data
                    customer = None
                    if platform_customer_id:
                        customer = await get_customer_by_platform_id(db, store.id, platform_customer_id)
                    
                    if customer:
                        order_db_data['customer_id'] = customer.id
                    else:
                        order_db_data['customer_id'] = None # Or handle as needed if customer must exist
                        logger.warning(f"Customer with platform ID {platform_customer_id} not found for store {store_id} while processing order {order_data_raw.get('id')}.")

                    # Extract line items (assuming map_order_to_db_model includes them or they need separate mapping)
                    line_items_raw = order_data_raw.get('line_items', [])
                    mapped_line_items = [
                        await connector.map_line_item_to_db_model(item) for item in line_items_raw
                    ]
                    order_db_data['line_items'] = mapped_line_items # Pass mapped items to upsert

                    await upsert_order(db, order_db_data)
                except Exception as e:
                    logger.error(f"Error processing order {order_data_raw.get('id')} for store {store_id}: {e}", exc_info=True)
            await db.commit() # Commit after each batch

        # 5. Update Last Sync Time
        store.last_sync_at = datetime.utcnow()
        db.add(store)
        await db.commit()
        logger.info(f"Successfully completed periodic sync for store_id: {store_id}")
        return f"Periodic sync completed for store {store_id}."

    except Exception as exc:
        logger.error(f"Periodic sync failed for store {store_id}: {exc}", exc_info=True)
        await db.rollback() # Rollback on failure
        try:
            # Retry the task with exponential backoff
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.critical(f"Periodic sync for store {store_id} failed after max retries.")
            # Optionally, mark the store sync status as failed in the DB
            return f"Periodic sync failed permanently for store {store_id}."
    finally:
        # Ensure the database session is properly closed if it's still active
        if db and db.is_active:
            try:
                await db.close()
                logger.info(f"Database session closed for store_id: {store_id}")
            except Exception as e:
                logger.error(f"Error closing database session for store_id {store_id}: {e}", exc_info=True)

# --- Periodic Sync Task ---
@celery_async_task()
async def periodic_sync_store(self, store_id: UUID):
    """Task for periodically syncing data for a specific store."""
    async with AsyncSessionLocal() as db:
        return await _periodic_sync_logic(self, store_id, db)



# --- Scheduler Task --- 
async def _schedule_periodic_syncs_logic():
    """Logic for fetching all active stores and scheduling periodic_sync_store for each.
    This function queries all active stores and schedules a periodic sync task for each one.
    """
    logger.info("Starting to schedule periodic syncs for all active stores")
    try:
        async with AsyncSessionLocal() as db:
            # Query all active stores
            result = await db.execute(select(Store).where(Store.is_active == True))
            stores = result.scalars().all()
            if not stores:
                logger.info("No active stores found for periodic sync scheduling.")
                return "No active stores found."
            # Schedule a periodic sync task for each active store
            scheduled_count = 0
            for store in stores:
                try:
                    # Schedule the periodic sync task
                    # The task will be executed asynchronously by Celery
                    periodic_sync_store.delay(store.id)
                    scheduled_count += 1
                    logger.info(f"Scheduled periodic sync for store {store.id}")
                except Exception as e:
                    logger.error(f"Failed to schedule periodic sync for store {store.id}: {e}", exc_info=True)
            logger.info(f"Scheduled periodic syncs for {scheduled_count} stores.")
            return f"Scheduled periodic syncs for {scheduled_count} stores."
    except Exception as exc:
        logger.error(f"Failed to schedule periodic syncs: {exc}", exc_info=True)
        return f"Failed to schedule periodic syncs: {exc}"

@celery_async_task()
async def schedule_periodic_syncs(self, *args, **kwargs):
    """Task for fetching all active stores and scheduling periodic_sync_store for each."""
    
    await _schedule_periodic_syncs_logic()
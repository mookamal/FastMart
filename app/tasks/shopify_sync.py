import logging
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from app.tasks.celery_app import celery_app
from app.db.models import Store, Product, Customer, Order, LineItem
from app.services.platform_connector import get_connector
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import asyncio
from app.db.base import AsyncSessionLocal
from asgiref.sync import async_to_sync
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

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60*5)
def initial_sync_store(self, store_id: UUID):
    def run_async():
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                        
            async def _run():
                async with AsyncSessionLocal() as db:
                    try:
                        result = await sync_store_logic(self, store_id, db)
                        return result
                    except Exception as e:
                        logger.error(f"Error in _run for store {store_id}: {e}", exc_info=True)
                        raise
            
            return loop.run_until_complete(_run())
        except Exception as e:
            logger.error(f"Error in run_async for store {store_id}: {e}", exc_info=True)
            raise

    return run_async()

    
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def periodic_sync_store(self, store_id: int):
    """Periodically syncs data for a specific store since the last sync."""
    import asyncio
    from app.db.base import AsyncSessionLocal
    
    def run_async():
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            async def _run():
                async with AsyncSessionLocal() as db:
                    try:
                        return await _periodic_sync_logic(self, store_id, db)
                    except Exception as e:
                        logger.error(f"Error in _run for periodic sync of store {store_id}: {e}", exc_info=True)
                        raise
            
            return loop.run_until_complete(_run())
        except Exception as e:
            logger.error(f"Error in run_async for periodic sync of store {store_id}: {e}", exc_info=True)
            raise
    
    return run_async()

async def _periodic_sync_logic(self, store_id: int, db: AsyncSession):
    """Logic for periodically syncing data for a specific store."""
    logger.info(f"Starting periodic sync for store_id: {store_id}")
    
    # Ensure db is valid and connected
    if db.is_active:
        logger.info(f"Database session is active for periodic sync of store_id: {store_id}")
    else:
        logger.error(f"Database session is not active for periodic sync of store_id: {store_id}")
        return f"Database session not active for periodic sync of store {store_id}."
    
    try:
        result = await db.execute(select(Store).where(Store.id == store_id))
        store = result.scalars().first()

        if not store:
            logger.info(f"Store with id {store_id} not found.")
            return
        if not store.is_active:
            logger.info(f"Store {store.name} (id: {store_id}) is inactive. Skipping periodic sync.")
            return
        if not store.platform:
             logger.info(f"Store {store.name} (id: {store_id}) has no platform defined. Skipping sync.")
             return

        connector = get_connector(store.platform)

        # Determine the 'since' timestamp for fetching updates
        since = None
        if store.last_sync_at:
            # Go back a bit further to avoid missing data due to timing issues/clock skew
            since = store.last_sync_at - timedelta(minutes=5)
            # Ensure 'since' is timezone-aware (UTC) if last_sync_at is
            if store.last_sync_at.tzinfo is None:
                 # Assuming last_sync_at was stored as naive UTC
                 since = timezone.utc.localize(since) 
            logger.info(f"Syncing store {store.name} (id: {store_id}) since {since.isoformat()}")
        else:
            # If never synced, maybe trigger initial sync or log a warning?
            # For now, we'll just log and potentially fetch everything (since=None)
            logger.info(f"Store {store.name} (id: {store_id}) has no last_sync_at. Performing full fetch for periodic sync.")
            # Alternatively, could call initial_sync_store.delay(store_id) and return

        # --- Fetch Updated Data --- 
        # Note: Adapt the UPSERT logic from initial_sync_store
        # The connector methods need to accept the 'since' parameter

        logger.info(f"Fetching updated customers for store {store_id} since {since}")
        updated_customers_data = await connector.fetch_customers(access_token=store.access_token, shop_domain=store.shop_domain, since=since)
        for customer_data_raw in updated_customers_data:
            try:
                customer_db_data = connector.map_customer_to_db_model(customer_data_raw,store.id)
                await upsert_customer(db, customer_db_data)
            except Exception as e:
                logger.error(f"Error processing customer {customer_data_raw.get('id')} for store {store_id}: {e}", exc_info=True)
        await db.commit()

        logger.info(f"Fetching updated products for store {store_id} since {since}")
        updated_products_data = await connector.get_products(since=since)
        # TODO: Implement UPSERT logic for products
        logger.info(f"Fetched {len(updated_products_data)} updated products.")
        # Example placeholder for UPSERT:
        # for product_data in updated_products_data:
        #     await upsert_product(db, store_id, product_data)

        logger.info(f"Fetching updated orders for store {store_id} since {since}")
        updated_orders_data = await connector.get_orders(since=since)
        # TODO: Implement UPSERT logic for orders and relationships
        logger.info(f"Fetched {len(updated_orders_data)} updated orders.")
        # Example placeholder for UPSERT:
        # for order_data in updated_orders_data:
        #     await upsert_order(db, store_id, order_data)

        # --- Update Last Sync Timestamp --- 
        store.last_sync_at = datetime.now(timezone.utc) # Use timezone-aware datetime
        db.add(store)
        await db.commit()
        logger.info(f"Successfully completed periodic sync for store_id: {store_id}")

    except Exception as e:
        await db.rollback()
        logger.error(f"Error during periodic sync for store_id {store_id}: {e}", exc_info=True)
        # Retry the task using Celery's built-in mechanism
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.critical(f"Periodic sync for store {store_id} failed after max retries.")
            return f"Periodic sync failed permanently for store {store_id}."
    finally:
        # Ensure the database session is properly closed if it's still active
        if db and db.is_active:
            try:
                await db.close()
                logger.info(f"Database session closed for store_id: {store_id}")
            except Exception as e:
                logger.error(f"Error closing database session for store_id {store_id}: {e}", exc_info=True)

# --- Scheduler Task --- 

@celery_app.task
def schedule_periodic_syncs():
    """Fetches all active stores and schedules periodic_sync_store for each."""
    import asyncio
    from app.db.base import AsyncSessionLocal
    
    def run_async():
        try:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            async def _run():
                async with AsyncSessionLocal() as db:
                    try:
                        return await _schedule_periodic_syncs_logic(db)
                    except Exception as e:
                        logger.error(f"Error in _run for schedule_periodic_syncs: {e}", exc_info=True)
                        raise
            
            return loop.run_until_complete(_run())
        except Exception as e:
            logger.error(f"Error in run_async for schedule_periodic_syncs: {e}", exc_info=True)
            raise
    
    return run_async()

async def _schedule_periodic_syncs_logic(db: AsyncSession):
    """Logic for fetching all active stores and scheduling periodic_sync_store for each."""
    logger.info("Running scheduler task: schedule_periodic_syncs")
    
    # Ensure db is valid and connected
    if db.is_active:
        logger.info("Database session is active for schedule_periodic_syncs")
    else:
        logger.error("Database session is not active for schedule_periodic_syncs")
        return "Database session not active for schedule_periodic_syncs."
    
    try:
        result = await db.execute(select(Store).where(Store.is_active == True))
        active_stores = result.scalars().all()
        
        logger.info(f"Found {len(active_stores)} active stores to schedule sync for.")
        for store in active_stores:
            logger.info(f"Scheduling periodic sync for store: {store.name} (id: {store.id})")
            periodic_sync_store.delay(store.id)
            
    except Exception as e:
        logger.error(f"Error in scheduler task: {e}", exc_info=True)
        # Consider logging this error more formally
    finally:
        # Ensure the database session is properly closed if it's still active
        if db and db.is_active:
            try:
                await db.close()
                logger.info("Database session closed for schedule_periodic_syncs")
            except Exception as e:
                logger.error(f"Error closing database session for schedule_periodic_syncs: {e}", exc_info=True)
from locale import currency
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.models.store import Store
from app.schemas.store import StoreCreate

async def create_or_update_store(db: AsyncSession, store: StoreCreate) -> Store:
    """Creates a new store or updates an existing one based on user_id and domain."""
    
    # Check if a store already exists for this user and domain
    stmt = select(Store).where(
        Store.user_id == store.user_id, 
        Store.shop_domain == store.domain # Use 'domain' from StoreCreate which maps to 'shop_domain'
    )
    result = await db.execute(stmt)
    db_store = result.scalars().first()

    if db_store:
        # Update existing store
        db_store.access_token = store.access_token # Setter handles encryption
        db_store.scope = store.scope
        db_store.is_active = store.is_active
        db_store.currency = store.currency
        # updated_at is handled by onupdate=func.now()
    else:
        # Create new store
        db_store = Store(
            user_id=store.user_id,
            platform=store.platform,
            shop_domain=store.domain,
            access_token=store.access_token, # Setter handles encryption
            scope=store.scope,
            is_active=store.is_active,
            currency=store.currency
        )
        db.add(db_store)

    await db.commit()
    await db.refresh(db_store)
    return db_store
from uuid import UUID
from strawberry.types import Info
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user
from app.db.models.store import Store as StoreModel
from app.services.platform_connector import get_connector
from app.tasks.shopify_sync import initial_sync_store



async def resolve_disconnect_store(info: Info, store_id: str) -> bool:
    """
    Resolver for the disconnectStore mutation.
    This sets a store to inactive rather than deleting it.
    """
    # Get context from the GraphQL request
    context = info.context
    db: AsyncSession = context["db"]
    
    # Get the current authenticated user
    current_user = await get_current_user(context["request"], db)
    if not current_user:
        raise ValueError("Authentication required")
    
    try:
        # Get the store
        store_model = await db.get(StoreModel, UUID(store_id))
        if not store_model:
            raise ValueError("Store not found")
        
        # Verify ownership
        if store_model.user_id != current_user.id:
            raise ValueError("Unauthorized: You don't own this store")
        
        # Set the store to inactive
        store_model.is_active = False
        db.add(store_model)
        await db.commit()
        
        return True
        
    except ValueError as e:
        raise ValueError(f"Failed to disconnect store: {str(e)}")
    except Exception as e:
        raise ValueError(f"An error occurred while disconnecting the store: {str(e)}")

async def resolve_trigger_store_sync(info: Info, store_id: str) -> bool:
    """
    Resolver for the triggerStoreSync mutation.
    This manually triggers a store sync operation.
    """
    # Get context from the GraphQL request
    context = info.context
    db: AsyncSession = context["db"]
    
    # Get the current authenticated user
    current_user = await get_current_user(context["request"], db)
    if not current_user:
        raise ValueError("Authentication required")
    
    try:
        # Get the store
        store_model = await db.get(StoreModel, UUID(store_id))
        if not store_model:
            raise ValueError("Store not found")
        
        # Verify ownership
        if store_model.user_id != current_user.id:
            raise ValueError("Unauthorized: You don't own this store")
        
        # Verify the store is active
        if not store_model.is_active:
            raise ValueError("Cannot sync an inactive store")
        
        # Trigger the sync task
        initial_sync_store.delay(store_model.id)
        # for testing
        # example_task.delay()

        
        return True
        
    except ValueError as e:
        raise ValueError(f"Failed to trigger store sync: {str(e)}")
    except Exception as e:
        raise ValueError(f"An error occurred while triggering store sync: {str(e)}")

async def resolve_gen_link_shopify(info: Info, shop_domain: str) -> str:
    """
    Resolver for the genLinkShopify mutation.
    This generates a link to the Shopify app installation page.
    """
    # Get context from the GraphQL request
    context = info.context
    db: AsyncSession = context["db"]
    
    # Get the current authenticated user
    current_user = await get_current_user(context["request"], db)
    # Get the Shopify connector
    connector = get_connector('shopify')

    # gen auth url
    auth_url = await connector.generate_auth_url(shop_domain,current_user.id)

    return auth_url
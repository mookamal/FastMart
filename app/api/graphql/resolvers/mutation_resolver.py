from typing import Dict, Any
from uuid import UUID

from strawberry.types import Info
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.models.store import Store as StoreModel
from app.api.graphql.schema import Store
from app.schemas.store import StoreCreate
from app.crud.store import create_or_update_store
from app.services.platform_connector import get_connector
from app.core.security import encrypt_token
from app.tasks.shopify_sync import initial_sync_store

async def resolve_connect_shopify_store(info: Info, authorization_code: str, shop_domain: str) -> Store:
    """
    Resolver for the connectShopifyStore mutation.
    This creates a new Shopify store connection using the OAuth flow.
    """
    # Get context from the GraphQL request
    context = info.context
    db: AsyncSession = context["db"]
    
    # Get the current authenticated user
    current_user = await get_current_user(context["request"], db)
    if not current_user:
        raise ValueError("Authentication required")
    
    try:
        # Get the Shopify connector
        connector = get_connector('shopify')
        
        # Exchange the authorization code for an access token
        token_data = await connector.exchange_code_for_token(code=authorization_code, shop_domain=shop_domain)
        access_token = token_data.get('access_token')
        scope = token_data.get('scope')
        
        if not access_token:
            raise ValueError("Failed to obtain access token from Shopify")
        
        # Encrypt the access token for storage
        encrypted_token = encrypt_token(access_token)
        
        # Create or update the store record
        store_data = StoreCreate(
            user_id=current_user.id,
            platform="shopify",
            domain=shop_domain,
            access_token=encrypted_token,
            scope=scope,
            is_active=True
        )
        
        db_store = await create_or_update_store(db=db, store=store_data)
        
        # Dispatch Celery task for initial data sync
        initial_sync_store.delay(str(db_store.id))
        
        # Return the GraphQL Store type
        return Store(
            id=str(db_store.id),
            platform=db_store.platform,
            shop_domain=db_store.shop_domain,
            is_active=db_store.is_active,
            last_sync_at=db_store.last_sync_at,
            created_at=db_store.created_at
        )
        
    except ValueError as e:
        raise ValueError(f"Failed to connect Shopify store: {str(e)}")
    except Exception as e:
        raise ValueError(f"An error occurred while connecting the Shopify store: {str(e)}")

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
        initial_sync_store.delay(str(store_model.id))
        
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
    # Get the Shopify connector
    connector = get_connector('shopify')

    # gen auth url
    auth_url = await connector.generate_auth_url(shop_domain)

    return auth_url
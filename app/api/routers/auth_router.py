from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict
import uuid

from app.services.platform_connector import get_connector
from app.core.security import encrypt_token
# TODO: Import database session and store CRUD operations
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud.store import create_or_update_store
from app.schemas.store import StoreCreate, Store

router = APIRouter()

@router.get("/auth/shopify/callback", response_model=Dict) # TODO: Define a proper response model later
async def handle_shopify_callback(
    code: str = Query(...),
    shop: str = Query(...),
    # state: str = Query(...), # Optional: For associating with user session/request
    db: AsyncSession = Depends(get_db)
):
    """Handles the redirect callback from Shopify after OAuth authorization."""
    try:
        # 1. Get the Shopify connector
        connector = get_connector('shopify')

        # 2. Exchange the code for an access token
        token_data = await connector.exchange_code_for_token(code=code, shop_domain=shop)
        access_token = token_data.get('access_token')
        scope = token_data.get('scope')

        if not access_token:
            raise HTTPException(status_code=400, detail="Could not retrieve access token from Shopify")

        # 3. Encrypt the access token
        encrypted_token = encrypt_token(access_token)

        # 4. Associate with user (Placeholder - needs implementation)
        # TODO: Replace with actual user ID retrieval (e.g., from JWT token or state)
        user_id = uuid.uuid4() # Placeholder UUID

        # 5. Create or update the store record in the database
        store_data = StoreCreate(
            user_id=user_id,
            platform="shopify",
            domain=shop,
            access_token=encrypted_token,
            scope=scope,
            is_active=True
        )
        db_store = await create_or_update_store(db=db, store=store_data)

        # 6. Dispatch Celery task for initial sync
        from app.tasks.shopify_sync import initial_sync_store
        initial_sync_store.delay(db_store.id)

        # 7. Return success response
        return {
            "message": "Shopify store connected successfully! Initial data sync started.",
            "shop_domain": shop,
            "store_id": db_store.id
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Log the exception details for debugging
        print(f"Error during Shopify callback: {e}") # Replace with proper logging
        raise HTTPException(status_code=500, detail=f"An error occurred during the Shopify callback process: {str(e)}")
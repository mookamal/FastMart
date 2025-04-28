from fastapi import APIRouter, Depends, HTTPException, Query, status, Form,Request
from fastapi.security import OAuth2PasswordRequestForm

class EmailPasswordForm(OAuth2PasswordRequestForm):
    def __init__(
        self,
        email: str = Form(...),
        password: str = Form(...),
    ):
        super().__init__(username=email, password=password)

from typing import Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.platform_connector import get_connector
from app.core.security import encrypt_token
from app.db.base import get_db
from app.crud.store import create_or_update_store
from app.schemas.store import StoreCreate, Store
from app.services.auth_service import authenticate_user, create_user, create_user_token

router = APIRouter()

@router.post("/auth/token", response_model=Dict[str, Any])
async def login_for_access_token(
    form_data: EmailPasswordForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Get an access token for future authenticated requests.
    """
    # NOTE: username here is email
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await create_user_token(user)

@router.post("/auth/register", response_model=Dict[str, Any])
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    """
    user = await create_user(email, password, db)
    return {
        "id": user.id,
        "email": user.email,
        "message": "User registered successfully"
    }

@router.get("/auth/shopify/callback", response_model=Dict) # TODO: Define a proper response model later
async def handle_shopify_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handles the redirect callback from Shopify after OAuth authorization."""
    try:
        params = dict(request.query_params)
        shop = params.get('shop')
        # 1. Get the Shopify connector
        connector = get_connector('shopify')

        # 2. Exchange the code for an access token
        token_data = await connector.exchange_code_for_token(params)
        access_token = token_data.get('access_token')
        scope = token_data.get('scope')

        if not access_token:
            raise HTTPException(status_code=400, detail="Could not retrieve access token from Shopify")

        # 3. Encrypt the access token
        encrypted_token = encrypt_token(access_token)

        # 4. Associate with user (Placeholder - needs implementation)
        # TODO: Replace with actual user ID retrieval (e.g., from JWT token or state)
        user_id = "1dc93b23-4bb7-429a-8b1e-7ee25f82b389" # Placeholder UUID

        # 5. Create or update the store record in the database
        store_data = StoreCreate(
            user_id=user_id,
            platform="shopify",
            domain=shop,
            access_token=encrypted_token,
            scope=str(scope),
            is_active=True
        )
        db_store = await create_or_update_store(db=db, store=store_data)

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
from fastapi import APIRouter, Depends, HTTPException, status, Form,Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse

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
from app.core.security import encrypt_token,verify_secure_state
from app.db.base import get_db
from app.crud.store import create_or_update_store
from app.schemas.store import StoreCreate
from app.services.auth_service import authenticate_user, create_user, create_user_token
from app.tasks.shopify_sync import initial_sync_store
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
        state = params.get('state')
        state_data = verify_secure_state(state)
        user_id = state_data.get('user_id')  # Retrieve user_id from state_data
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in state")
        

        # 5. Create or update the store record in the database
        store_data = StoreCreate(
            user_id=uuid.UUID(user_id),
            platform="shopify",
            domain=shop,
            access_token=encrypted_token,
            scope=str(scope),
            is_active=True
        )
        db_store = await create_or_update_store(db=db, store=store_data)

        # 6. Trigger the initial sync
        initial_sync_store.delay(db_store.id)

        # 7. Redirect to the frontend
        frontend_url = f"http://localhost:3000/shopify-callback?store_id={db_store.id}&shop={shop}"
        return RedirectResponse(url=frontend_url)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Log the exception details for debugging
        print(f"Error during Shopify callback: {e}") # Replace with proper logging
        raise HTTPException(status_code=500, detail=f"An error occurred during the Shopify callback process: {str(e)}")
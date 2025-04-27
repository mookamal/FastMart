from typing import List
from uuid import UUID

from strawberry.types import Info
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user import User as UserModel
from app.db.models.store import Store as StoreModel
from app.api.graphql.schema import User, Store
from app.core.auth import get_current_user

async def resolve_me(info: Info) -> User:
    """Resolver for the me query that returns the authenticated user."""
    # Get the current user from the request context
    # This will be implemented with proper authentication later
    context = info.context
    db: AsyncSession = context["db"]
    
    # For now, we'll use a placeholder implementation
    # In a real implementation, we would get the user ID from the authentication token
    current_user = await get_current_user(context["request"])
    
    # Query the database for the user
    user_model = await db.get(UserModel, current_user.id)
    if not user_model:
        raise ValueError("User not found")
    
    # Convert the model to a GraphQL type
    return User(
        id=str(user_model.id),
        email=user_model.email,
        created_at=user_model.created_at
    )

async def resolve_user_stores(user: User, info: Info) -> List[Store]:
    """Resolver for the stores field on the User type."""
    context = info.context
    db: AsyncSession = context["db"]
    
    # Query the database for the user's stores
    stmt = select(StoreModel).where(StoreModel.user_id == UUID(user.id))
    result = await db.execute(stmt)
    store_models = result.scalars().all()
    
    # Convert the models to GraphQL types
    return [
        Store(
            id=str(store.id),
            platform=store.platform,
            shop_domain=store.shop_domain,
            is_active=store.is_active,
            last_sync_at=store.last_sync_at,
            created_at=store.created_at
        ) for store in store_models
    ]
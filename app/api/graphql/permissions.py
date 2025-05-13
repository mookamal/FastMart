import strawberry
from typing import Any, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, CurrentUser
from app.db.models.store import Store as StoreModel


class StoreOwnerPermission(strawberry.BasePermission):
    message = "User is not authorized to access this store"
    
    def __init__(self):
        self.current_user: Optional[CurrentUser] = None
    
    async def has_permission(
        self, 
        source: Any, 
        info: strawberry.types.Info, 
        **kwargs
    ) -> bool:
        # Get the database session from the context
        context = info.context
        db: AsyncSession = context["db"]
        
        # Get the current user from the request context
        try:
            self.current_user = await get_current_user(context["request"], db)
        except Exception:
            return False
        
        # Get the store_id from the arguments
        store_id = kwargs.get("store_id")
        if not store_id:
            return False
        
        # Query the database to check if the user owns the store
        try:
            # Convert string ID to UUID if needed
            if isinstance(store_id, str):
                store_id = UUID(store_id)
                
            # Query the store
            stmt = select(StoreModel).where(
                StoreModel.id == store_id,
                StoreModel.user_id == self.current_user.id
            )
            result = await db.execute(stmt)
            store = result.scalars().first()
            
            # If store exists and belongs to the user, permission is granted
            return store is not None
        except Exception:
            return False
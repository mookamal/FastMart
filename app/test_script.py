import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.base import get_db
from uuid import UUID
from app.db.models import Store
from app.core.security import decrypt_token

STORE_ID_FOR_TESTING = UUID("4582ebc2-660b-4dec-92fc-077988087395")

async def get_store_access_token(store_id: UUID):
    from sqlalchemy import select
    async for db in get_db():
        result = await db.execute(select(Store).where(Store.id == str(store_id)))
        store = result.scalars().first()
        if store:
            return store.access_token
    return None

if __name__ == "__main__":
    import asyncio
    token = asyncio.run(get_store_access_token(STORE_ID_FOR_TESTING))
    token = decrypt_token(token)
    print(f"Access Token: {token}")
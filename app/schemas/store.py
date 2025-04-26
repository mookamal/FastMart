from pydantic import BaseModel, HttpUrl
from typing import Optional
import uuid

# Base model for common attributes
class StoreBase(BaseModel):
    user_id: uuid.UUID
    platform: str
    domain: str
    scope: Optional[str] = None
    is_active: bool = True

# Model for creating a new store (input)
class StoreCreate(StoreBase):
    access_token: str # Encrypted token

# Model for reading store data (output, includes ID)
class Store(StoreBase):
    id: int
    access_token: str # Keep encrypted token here as well for retrieval if needed

    class Config:
        orm_mode = True # Enable ORM mode for SQLAlchemy compatibility
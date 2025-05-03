from typing import Any, Dict, TypeVar, Generic, Optional, List, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from strawberry.types import Info

T = TypeVar('T')  # Type for the database model
G = TypeVar('G')  # Type for the GraphQL type

class BaseResolver(Generic[T, G]):
    """Base resolver class to standardize resolver patterns across all domain modules."""
    
    model_class: Type[T] = None
    graphql_type_class: Type[G] = None
    
    @classmethod
    async def get_by_id(cls, id: str, db: AsyncSession) -> Optional[T]:
        """Get a model instance by ID."""
        try:
            return await db.get(cls.model_class, UUID(id))
        except Exception as e:
            raise ValueError(f"Error retrieving {cls.model_class.__name__}: {str(e)}")
    
    @classmethod
    async def get_all(cls, db: AsyncSession, **filters) -> List[T]:
        """Get all model instances with optional filters."""
        try:
            query = select(cls.model_class)
            
            # Apply filters if provided
            for key, value in filters.items():
                if hasattr(cls.model_class, key) and value is not None:
                    query = query.where(getattr(cls.model_class, key) == value)
            
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            raise ValueError(f"Error retrieving {cls.model_class.__name__} list: {str(e)}")
    
    @classmethod
    def to_graphql_type(cls, model: T) -> G:
        """Convert a database model to a GraphQL type."""
        raise NotImplementedError("Subclasses must implement to_graphql_type method")
    
    @classmethod
    def get_db_from_info(cls, info: Info) -> AsyncSession:
        """Extract database session from GraphQL info context."""
        context = info.context
        return context.get("db")
from typing import Any, Dict

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import strawberry
from strawberry.fastapi import GraphQLRouter

from app.api.graphql.schema import schema
from app.db.base import get_db

async def get_context(request: Request, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Creates a context for GraphQL resolvers with request and database session.
    """
    return {
        "request": request,
        "db": db
    }

# Create a GraphQL router for FastAPI
graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True  # Enable GraphiQL interface for development
)
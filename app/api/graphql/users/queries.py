import strawberry
from strawberry.types import Info
from app.api.graphql.users.types import User

@strawberry.type
class UserQuery:
    @strawberry.field
    async def me(self, info: Info) -> User:
        from app.api.graphql.resolvers.user_resolver import resolve_me
        return await resolve_me(info)
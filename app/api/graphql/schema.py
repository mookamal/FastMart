from typing import List, Optional
import strawberry
from strawberry.scalars import ID

# Import feature queries and mutations
from app.api.graphql.users.queries import UserQuery
from app.api.graphql.users.mutations import UserMutation
from app.api.graphql.stores.queries import StoreQuery
from app.api.graphql.stores.mutations import StoreMutation
from app.api.graphql.products.queries import ProductQuery
from app.api.graphql.products.mutations import ProductMutation
from app.api.graphql.orders.queries import OrderQuery
from app.api.graphql.customers.queries import CustomerQuery
from app.api.graphql.orders.mutations import OrderMutation
from app.api.graphql.analytics.queries import AnalyticsQuery

# Define root Query type by combining all feature queries
@strawberry.type
class Query(UserQuery, StoreQuery, ProductQuery, OrderQuery, AnalyticsQuery,CustomerQuery):
    pass

# Define root Mutation type by combining all feature mutations
@strawberry.type
class Mutation(UserMutation, StoreMutation, ProductMutation, OrderMutation):
    pass

# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
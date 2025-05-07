# GraphQL Permission System

## Overview

This document describes the permission system implemented for the GraphQL API in the analytics project. The permission system ensures that users can only access and modify stores that they own.

## Implementation

The permission system is implemented using Strawberry's permission classes. The main permission class is `StoreOwnerPermission`, which checks if the current user owns the store being accessed.

### StoreOwnerPermission

The `StoreOwnerPermission` class is defined in `app/api/graphql/permissions.py`. It extends Strawberry's `BasePermission` class and implements the `has_permission` method to check if the current user owns the store being accessed.

The permission check works as follows:

1. Get the current user from the request context using the `get_current_user` function
2. Extract the store ID from the query/mutation arguments
3. Query the database to check if the store exists and belongs to the current user
4. Return `True` if the store exists and belongs to the current user, `False` otherwise

### Usage

The permission class is applied to GraphQL fields using the `permission_classes` parameter of the `@strawberry.field` and `@strawberry.mutation` decorators.

For example:

```python
@strawberry.field(permission_classes=[StoreOwnerPermission])
async def store(self, info: Info, id: ID) -> Store:
    # Resolver implementation
```

```python
@strawberry.mutation(permission_classes=[StoreOwnerPermission])
async def disconnect_store(self, info: Info, store_id: ID) -> bool:
    # Resolver implementation
```

### Applied Permissions

The `StoreOwnerPermission` class is applied to the following GraphQL fields:

- `store` query - Ensures users can only view stores they own
- `disconnect_store` mutation - Ensures users can only disconnect stores they own
- `trigger_store_sync` mutation - Ensures users can only trigger syncs for stores they own

## Benefits

- **Centralized Permission Logic**: The permission logic is defined in a single place, making it easier to maintain and update
- **Declarative Approach**: Permissions are applied declaratively using decorators, making the code more readable
- **Reusable**: The permission class can be reused across different GraphQL fields
- **Separation of Concerns**: The permission logic is separated from the resolver logic, making the code more modular

## Future Improvements

- Add more granular permissions for different operations
- Implement role-based permissions for admin users
- Add caching to improve performance of permission checks
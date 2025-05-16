# Daily Sales Analytics Module

This module provides functionality for storing and loading precomputed daily sales analytics data in the database. It follows a layered architecture that clearly separates concerns across different components.

## Architecture

### Models (Database Storage)
- `DailySalesAnalytics`: Database model for storing precomputed daily sales metrics
  - Location: `app/db/models/daily_sales_analytics.py`
  - Fields: date, total_sales, total_orders, average_order_value, profit
  - Includes appropriate indexes for efficient querying

### Services (Calculating and Updating Data)
- `DailySalesAnalyticsService`: Service for calculating and managing analytics data
  - Location: `app/services/analytics/daily_sales_service.py`
  - Key methods:
    - `get_daily_analytics`: Retrieve analytics for a date range
    - `calculate_and_store_daily_analytics`: Calculate and store for a specific date
    - `update_analytics_for_date_range`: Process a range of dates

### Schemas (GraphQL Types)
- GraphQL type definitions for the analytics data
  - Location: `app/api/graphql/analytics/daily_sales_types.py`
  - Types:
    - `DailySalesAnalytics`: Individual daily record
    - `DailySalesAnalyticsSummary`: Aggregated data over a period

### Resolvers (GraphQL API)
- GraphQL resolvers for exposing the data
  - Location: `app/api/graphql/analytics/daily_sales_resolvers.py`
  - Query resolvers:
    - `resolve_daily_sales_analytics`: Get analytics for a date range
    - `resolve_daily_sales_analytics_summary`: Get summary for a date range
  - Mutation resolvers:
    - `resolve_update_daily_sales_analytics`: Update for a specific date
    - `resolve_update_daily_sales_analytics_range`: Update for a date range

## Usage

### GraphQL Queries
```graphql
query DailySalesAnalytics($storeId: ID!, $dateRange: DateRangeInput!) {
  dailySalesAnalytics(storeId: $storeId, dateRange: $dateRange) {
    date
    totalSales
    totalOrders
    averageOrderValue
    profit
  }
}

query DailySalesAnalyticsSummary($storeId: ID!, $dateRange: DateRangeInput!) {
  dailySalesAnalyticsSummary(storeId: $storeId, dateRange: $dateRange) {
    startDate
    endDate
    totalSales
    totalOrders
    averageOrderValue
    totalProfit
    dailyAnalytics {
      date
      totalSales
      totalOrders
    }
  }
}
```

## Extending the Module

To add more analytics modules in the future:

1. Create a new database model in `app/db/models/`
2. Create a corresponding service in `app/services/analytics/`
3. Define GraphQL types in `app/api/graphql/analytics/`
4. Implement resolvers for the new types
5. Add queries and mutations to the existing GraphQL schema

This modular approach ensures that new analytics features can be added without modifying existing code, following the Open/Closed Principle.
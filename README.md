# FastMart Analytics Platform

## Project Overview
FastMart is an e-commerce analytics platform that provides comprehensive data analysis capabilities for online stores. The platform integrates with e-commerce platforms (currently Shopify) to collect and analyze sales data, customer behavior, product performance, and discount effectiveness.

## Database Schema

The platform uses a PostgreSQL database with the following core models:

### Core Models

- **Customers**
  - Standard fields: id, email, first_name, last_name, orders_count, total_spent
  - Analytics fields: tags (Array) - for customer segmentation and targeting

- **Orders**
  - Standard fields: id, order_number, total_price, currency, financial_status, fulfillment_status
  - Analytics fields: discount_applications (JSONB) - detailed discount usage information

- **Products**
  - Standard fields: id, title, vendor, product_type
  - Analytics fields: inventory_levels (JSONB) - inventory tracking across locations

- **Line Items**
  - Standard fields: id, title, variant_title, sku, quantity, price
  - Analytics fields: total_discount, tax_lines, properties, fulfillment_status, requires_shipping, gift_card, taxable

## Analytics Capabilities

### Store Analytics
- **Analytics Summary**
  - Total sales
  - Order count
  - Average order value
  - New customer count

### Product Analytics
- **Top Selling Products**
  - Total quantity sold
  - Total revenue

### Product Variant Analytics
- **Per Variant Metrics**
  - Total units sold
  - Total revenue
  - Average selling price
  - Inventory level

### Discount Analytics
- **Discount Code Performance**
  - Usage count
  - Total discount amount
  - Total sales generated

### Time Series Analysis
- **Orders Over Time**
  - Supports different time intervals (daily, weekly, monthly)

## GraphQL API

The platform provides a GraphQL API for accessing analytics data with the following main queries:

- `analyticsSummary` - Overall store performance metrics
- `topSellingProducts` - Best performing products by quantity
- `productVariantAnalytics` - Detailed metrics for product variants
- `discountCodeAnalytics` - Performance metrics for discount codes

## Data Synchronization

The platform includes automated data synchronization from e-commerce platforms:

- Shopify connector for importing products, customers, orders, and line items
- Scheduled tasks for keeping data up-to-date
- Analytics-specific data enrichment during synchronization

## Current Development Status

The project has implemented:
- Core database models with analytics fields
- GraphQL API for analytics queries
- Data synchronization from Shopify
- Basic analytics resolvers for key metrics

Next development phases will focus on:
- Enhanced visualization components
- Advanced analytics algorithms
- Additional e-commerce platform integrations
- Customizable dashboards
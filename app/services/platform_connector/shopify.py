import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from decimal import Decimal
import shopify
from dotenv import load_dotenv
from shopify import ShopifyResource
from shopify.collection import PaginatedCollection

from .base import EcommercePlatformConnector
from app.core.security import decrypt_token,create_secure_state
import logging

logging.basicConfig(level=logging.DEBUG)
# Load environment variables
load_dotenv()

# Define a retry decorator for rate limiting
def retry_on_rate_limit(max_retries=3, delay=5):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except ConnectionError as e:
                    # Check if it's a rate limit error (status code 429)
                    # The shopify library might not expose status code directly in ShopifyError
                    # We might need to rely on error message content or assume certain errors are rate limits
                    # For simplicity, we'll retry on any ShopifyError for now, but refine if possible.
                    # A more robust check would inspect e.response.code if available.
                    if "exceeded call limit" in str(e).lower() or isinstance(e, ConnectionError):
                        retries += 1
                        if retries >= max_retries:
                            raise Exception(f"Shopify API rate limit exceeded after {max_retries} retries: {e}")
                        print(f"Rate limit hit. Retrying in {delay} seconds... ({retries}/{max_retries})")
                        time.sleep(delay)
                    else:
                        # Re-raise other Shopify errors immediately
                        raise e
                except Exception as e:
                    # Handle other potential exceptions during the API call
                    raise Exception(f"An unexpected error occurred during Shopify API call: {e}")
            # This line should technically be unreachable if max_retries > 0
            raise Exception("Max retries reached without success.")
        return wrapper
    return decorator

class ShopifyConnector(EcommercePlatformConnector):
    """Shopify platform connector implementation."""

    API_VERSION = '2025-04' # Use a recent, stable API version

    async def get_platform_name(self) -> str:
        return "shopify"

    async def exchange_code_for_token(self, params: dict) -> Dict:
        """
        Exchange authorization code for access token using Shopify OAuth.

        Args:
            code: The authorization code from Shopify OAuth
            shop_domain: The shop's domain (e.g., 'myshop.myshopify.com')

        Returns:
            Dict containing access_token and scope

        Raises:
            Exception if the exchange fails
        """
        api_key = os.getenv('SHOPIFY_API_KEY')
        api_secret = os.getenv('SHOPIFY_API_SECRET')

        if not api_key or not api_secret:
            raise Exception("Shopify API credentials not configured")

        try:
            # Initialize Shopify session
            shopify.Session.setup(api_key=api_key, secret=api_secret)
            session = shopify.Session(params.get("shop"), self.API_VERSION)

            # Exchange code for access token
            access_token = session.request_token(params)
            # It's good practice to fetch the shop details to confirm connection
            shopify.ShopifyResource.activate_session(session)
            shop = shopify.Shop.current() # This confirms the token works
            shop_data = shop.to_dict()
            # shopify.ShopifyResource.clear_session()
            return {
                'access_token': access_token,
                'scope': [] ,
                'currency': shop_data['currency']
            }
        except ConnectionError as e:
            raise Exception(f"Failed to exchange code for token (Shopify API Error): {str(e)}")
        except Exception as e:
            # Catch other potential errors (network issues, etc.)
            raise Exception(f"Failed to exchange code for token (General Error): {str(e)}")

    async def get_api_client(self, access_token: str, shop_domain: str) -> shopify:
        """Get and activate a Shopify API client instance."""
        decrypted_token = decrypt_token(access_token) # Use the decrypted token
        if not decrypted_token:
            raise ValueError("Invalid or missing access token after decryption.")

        try:
            session = shopify.Session(shop_domain,self.API_VERSION ,decrypted_token)
            shopify.ShopifyResource.activate_session(session)
            return shopify
        except ValueError as e:
             raise Exception(f"Failed to activate Shopify session (maybe invalid token?): {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to initialize Shopify client: {str(e)}")

    @retry_on_rate_limit()
    async def _fetch_all_resources(self, resource_class: ShopifyResource, since: Optional[datetime] = None, limit: int = 50, **kwargs) -> List[Dict]:
        """Generic method to fetch all pages of a resource."""
        all_resources_data = []
        params = {'limit': min(limit, 250)} # Shopify max limit is 250
        if since:
            # Format datetime to ISO 8601 string for Shopify API
            params['updated_at_min'] = since.isoformat()

        params.update(kwargs) # Add any extra specific params

        resources: PaginatedCollection = resource_class.find(**params)
        while True:
            for resource in resources:
                all_resources_data.append(resource.to_dict())

            if not resources.has_next_page():
                break

            # Fetch the next page
            try:
                resources = resources.next_page()
            except ConnectionError as e:
                 # Handle potential errors during pagination itself (e.g., token expired mid-sync)
                 logging.error(f"Error fetching next page: {e}")
                 # Depending on the error, might want to break or retry
                 if "token" in str(e).lower(): # Basic check for token errors
                     raise Exception(f"Shopify token likely invalid during pagination: {e}")
                 # For now, re-raise other pagination errors after logging
                 raise e
            except Exception as e:
                logging.error(f"Unexpected error during pagination: {e}")
                raise e

        return all_resources_data

    async def fetch_orders(
        self,
        access_token: str,
        shop_domain: str,
        since: Optional[datetime] = None,
        limit: int = 50, # Note: this limit is per page, _fetch_all_resources handles pagination
        batch_size: int = 50
    ) -> List[Dict]:
        """Fetch orders from Shopify, handling pagination and rate limits."""
        client = await self.get_api_client(access_token, shop_domain)
        try:
            # Add status='any' to fetch orders regardless of status
            orders_data = await self._fetch_all_resources(
                client.Order,
                since=since,
                limit=limit,
                status='any' # Fetch all orders regardless of status
            )
            for i in range(0, len(orders_data), batch_size):
                yield orders_data[i:i + batch_size]
        except Exception as e:
            print(f"Error fetching Shopify orders for {shop_domain}: {e}")
            # Depending on requirements, might return empty list or re-raise
            raise e # Re-raise for now to signal failure
        finally:
            client.ShopifyResource.clear_session()
            # print(f"Shopify session cleared for {shop_domain}") # Debugging

    async def fetch_products(
        self,
        access_token: str,
        shop_domain: str,
        since: Optional[datetime] = None,
        limit: int = 50,
        batch_size: int = 50
    ) -> List[Dict]:
        """Fetch products from Shopify, handling pagination and rate limits."""
        client = await self.get_api_client(access_token, shop_domain)
        try:
            products_data = await self._fetch_all_resources(
                client.Product,
                since=since,
                limit=limit
            )
            for i in range(0, len(products_data), batch_size):
                yield products_data[i:i + batch_size]
        except Exception as e:
            print(f"Error fetching Shopify products for {shop_domain}: {e}")
            raise e
        finally:
            client.ShopifyResource.clear_session()

    async def fetch_customers(
        self,
        access_token: str,
        shop_domain: str,
        since: Optional[datetime] = None,
        limit: int = 50,
        batch_size: int = 50
    ) -> List[Dict]:
        """Fetch customers from Shopify, handling pagination and rate limits."""
        client = await self.get_api_client(access_token, shop_domain)
        try:
            customers_data = await self._fetch_all_resources(
                client.Customer,
                since=since,
                limit=limit
            )
            # Yield customers in batches
            for i in range(0, len(customers_data), batch_size):
                yield customers_data[i:i + batch_size]
        except Exception as e:
            print(f"Error fetching Shopify customers for {shop_domain}: {e}")
            raise e
        finally:
            client.ShopifyResource.clear_session()
            
    async def fetch_inventory_levels(
        self,
        access_token: str,
        shop_domain: str,
        limit: int = 250,
        batch_size: int = 50
    ) -> List[Dict]:
        """Fetch inventory levels from Shopify, handling pagination and rate limits.
        
        Note: Shopify's inventory_levels endpoint requires location_ids or inventory_item_ids
        as query parameters. This method fetches inventory items first, then gets their levels.
        """
        client = await self.get_api_client(access_token, shop_domain)
        try:
            all_inventory_levels = []
            
            if not all_inventory_levels:
                logging.info(f"No inventory levels found by location for {shop_domain}, trying alternative approach")
                try:
                    # Get a list of product variants first
                    variants = []
                    products = await self._fetch_all_resources(client.Product, limit=limit)
                    for product in products:
                        if 'variants' in product:
                            variants.extend(product.get('variants', []))
                    
                    # Get inventory item IDs from variants
                    inventory_item_ids = [variant.get('inventory_item_id') for variant in variants if variant.get('inventory_item_id')]
                    
                    # Fetch inventory levels in batches of inventory item IDs
                    for i in range(0, len(inventory_item_ids), batch_size):
                        batch_ids = inventory_item_ids[i:i + batch_size]
                        if batch_ids:
                            # Join IDs with commas for the API call
                            ids_param = ','.join(str(id) for id in batch_ids)
                            try:
                                levels = client.InventoryLevel.find(inventory_item_ids=ids_param)
                                for level in levels:
                                    all_inventory_levels.append(level.to_dict())
                            except Exception as batch_error:
                                logging.error(f"Error fetching inventory levels for batch: {batch_error}")
                except Exception as alt_approach_error:
                    logging.error(f"Alternative approach for inventory levels failed: {alt_approach_error}")
            
            # Yield all collected inventory levels in batches
            for i in range(0, len(all_inventory_levels), batch_size):
                yield all_inventory_levels[i:i + batch_size]
                
        except Exception as e:
            logging.error(f"Error fetching Shopify inventory levels for {shop_domain}: {e}")
            raise Exception(f"Failed to fetch inventory levels: {str(e)}")
        finally:
            client.ShopifyResource.clear_session()

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Safely parse ISO 8601 datetime strings from Shopify."""
        if not value:
            return None
        try:
            # Handle potential timezone offsets like -04:00 or Z
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            # Ensure datetime is timezone-aware (UTC)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            print(f"Warning: Could not parse datetime value: {value}")
            return None

    def _safe_decimal(self, value: Any) -> Decimal:
        """Safely convert value to Decimal, defaulting to 0.00."""
        if value is None:
            return Decimal('0.00')
        try:
            return Decimal(str(value))
        except Exception:
             print(f"Warning: Could not convert value to Decimal: {value}")
             return Decimal('0.00')

    async def map_order_to_db_model(
        self,
        platform_order_data: Dict,
        # store_id: uuid.UUID # store_id is handled by the caller/sync process
    ) -> Dict:
        """Transform Shopify order data into our database model format (excluding IDs)."""
        # Extract and process discount applications for analytics
        discount_applications = platform_order_data.get('discount_applications', [])
        # Ensure we capture all relevant discount data
        processed_discounts = []
        for discount in discount_applications:
            processed_discount = {
                'type': discount.get('type'),
                'value': discount.get('value'),
                'value_type': discount.get('value_type'),
                'allocation_method': discount.get('allocation_method'),
                'target_selection': discount.get('target_selection'),
                'target_type': discount.get('target_type'),
                'code': discount.get('code'),
                'title': discount.get('title')
            }
            processed_discounts.append(processed_discount)
            
        return {
            'platform_order_id': str(platform_order_data.get('id')),
            'order_number': str(platform_order_data.get('order_number')),
            'total_price': self._safe_decimal(platform_order_data.get('total_price')),
            'currency': platform_order_data.get('currency'),
            'financial_status': platform_order_data.get('financial_status'),
            'fulfillment_status': platform_order_data.get('fulfillment_status'), # Note: might be None
            'processed_at': self._parse_datetime(platform_order_data.get('processed_at')),
            'platform_created_at': self._parse_datetime(platform_order_data.get('created_at')),
            'platform_updated_at': self._parse_datetime(platform_order_data.get('updated_at')),
            # 'customer_id' needs to be looked up based on platform_customer_id
            'platform_customer_id': str(platform_order_data.get('customer', {}).get('id')) if platform_order_data.get('customer') else None,
            # Store processed discount applications for analytics
            'discount_applications': processed_discounts,
            'cancelled_at': self._parse_datetime(platform_order_data.get('cancelled_at')),
            # Line items need separate mapping and linking
            # 'line_items': platform_order_data.get('line_items', [])
        }

    async def map_product_to_db_model(
        self,
        platform_product_data: Dict,
    ) -> Dict:
        """Transform Shopify product data into our database model format (excluding IDs)."""
        return {
            'platform_product_id': str(platform_product_data.get('id')),
            'title': platform_product_data.get('title'),
            'vendor': platform_product_data.get('vendor'),
            'product_type': platform_product_data.get('product_type'),
            'platform_created_at': self._parse_datetime(platform_product_data.get('created_at')),
            'platform_updated_at': self._parse_datetime(platform_product_data.get('updated_at')),
            # Variants might need separate handling if storing variant-level details
            'variants': platform_product_data.get('variants', []) # Include variants for potential line item mapping
        }

    async def map_customer_to_db_model(
        self,
        platform_customer_data: Dict,
    ) -> Dict:
        """Transform Shopify customer data into our database model format (excluding IDs)."""
        return {
            'platform_customer_id': str(platform_customer_data.get('id')),
            'email': platform_customer_data.get('email'),
            'first_name': platform_customer_data.get('first_name'),
            'last_name': platform_customer_data.get('last_name'),
            'orders_count': int(platform_customer_data.get('orders_count', 0)),
            'total_spent': self._safe_decimal(platform_customer_data.get('total_spent')),
            'platform_created_at': self._parse_datetime(platform_customer_data.get('created_at')),
            'platform_updated_at': self._parse_datetime(platform_customer_data.get('updated_at')),
            'tags': platform_customer_data.get('tags', '').split(',') if platform_customer_data.get('tags') else [],
        }
    async def map_product_variant_to_db_model(
        self,
        platform_variant_data: Dict,
        # product_id: uuid.UUID # product_id is handled by the caller/sync process
    ) -> Dict:
        """Transform Shopify product variant data into our database model format (excluding IDs)."""
        return {
            'platform_variant_id': str(platform_variant_data.get('id')),
            'title': platform_variant_data.get('title'),
            'sku': platform_variant_data.get('sku'),
            'price': self._safe_decimal(platform_variant_data.get('price')),
            'compare_at_price': self._safe_decimal(platform_variant_data.get('compare_at_price')),
            'position': int(platform_variant_data.get('position', 1)),
            'inventory_item_id': str(platform_variant_data.get('inventory_item_id')) if platform_variant_data.get('inventory_item_id') else None,
            'inventory_quantity': int(platform_variant_data.get('inventory_quantity', 0)),
            'weight': self._safe_decimal(platform_variant_data.get('weight')),
            'weight_unit': platform_variant_data.get('weight_unit'),
            'option1': platform_variant_data.get('option1'),
            'option2': platform_variant_data.get('option2'),
            'option3': platform_variant_data.get('option3'),
            'taxable': platform_variant_data.get('taxable', True),
            'barcode': platform_variant_data.get('barcode'),
            'image_id': str(platform_variant_data.get('image_id')) if platform_variant_data.get('image_id') else None,
            'platform_created_at': self._parse_datetime(platform_variant_data.get('created_at')),
            'platform_updated_at': self._parse_datetime(platform_variant_data.get('updated_at')),
        }
    # Placeholder for line item mapping if needed later
    async def map_line_item_to_db_model(
        self,
        platform_line_item_data: Dict,
        # order_id: uuid.UUID, # Handled by caller
        # product_id: Optional[uuid.UUID] # Handled by caller (lookup)
    ) -> Dict:
         """Transform Shopify line item data into our database model format (excluding IDs)."""
         # Extract all relevant data for analytics
         return {
            'platform_line_item_id': str(platform_line_item_data.get('id')),
            'platform_product_id': str(platform_line_item_data.get('product_id')) if platform_line_item_data.get('product_id') else None,
            'platform_variant_id': str(platform_line_item_data.get('variant_id')) if platform_line_item_data.get('variant_id') else None,
            'title': platform_line_item_data.get('title'),
            'variant_title': platform_line_item_data.get('variant_title'),
            'sku': platform_line_item_data.get('sku'),
            'quantity': int(platform_line_item_data.get('quantity', 0)),
            'price': self._safe_decimal(platform_line_item_data.get('price')),
            # Additional fields for analytics
            'total_discount': self._safe_decimal(platform_line_item_data.get('total_discount')),
            'tax_lines': platform_line_item_data.get('tax_lines', []),
            'properties': platform_line_item_data.get('properties', []),
            'fulfillment_status': platform_line_item_data.get('fulfillment_status'),
            'requires_shipping': platform_line_item_data.get('requires_shipping', False),
            'gift_card': platform_line_item_data.get('gift_card', False),
            'taxable': platform_line_item_data.get('taxable', True)
         }
    # generate auth_url for shopify
    async def generate_auth_url(self, shop_domain: str,user_id: str = None) -> str:
        """Generate the URL for the Shopify OAuth flow."""
        api_key = os.getenv('SHOPIFY_API_KEY')
        secret = os.getenv('SHOPIFY_API_SECRET')

        if not api_key or not secret:
            raise Exception("Shopify API credentials not configured")

        shop_url = f"{shop_domain}.myshopify.com"
        # Initialize the session
        shopify.Session.setup(api_key=api_key, secret=secret)
        session = shopify.Session(shop_url, self.API_VERSION)

        scopes = ['read_products', 'read_orders','read_customers','read_inventory','read_fulfillments','read_locations']
        # Create a secure state parameter
        if user_id:
            state = create_secure_state(str(user_id))
        else:
            # Fallback for testing
            state = "test_state"
        redirect_uri  = "http://localhost:8000/api/v1/auth/shopify/callback"
        # Generate the URL
        auth_url = session.create_permission_url(scopes,redirect_uri, state)
        return auth_url
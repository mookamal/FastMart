from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict
import uuid

class EcommercePlatformConnector(ABC):
    """Abstract base class for e-commerce platform connectors."""
    
    @abstractmethod
    async def get_platform_name(self) -> str:
        """Get the name of the platform this connector handles."""
        pass
    
    @abstractmethod
    async def exchange_code_for_token(self, params: dict) -> Dict:
        """
        Exchange an authorization code for an access token.
        
        Args:
            code: The authorization code from the OAuth flow
            shop_domain: The shop's domain (e.g., 'myshop.myshopify.com')
            
        Returns:
            Dict containing access_token and scope
            
        Raises:
            Exception if the exchange fails
        """
        pass
    
    @abstractmethod
    async def fetch_orders(
        self, 
        access_token: str, 
        shop_domain: str, 
        since: Optional[datetime] = None, 
        limit: int = 50
    ) -> List[Dict]:
        """Fetch orders from the platform."""
        pass
    
    @abstractmethod
    async def fetch_products(
        self, 
        access_token: str, 
        shop_domain: str, 
        since: Optional[datetime] = None, 
        limit: int = 50
    ) -> List[Dict]:
        """Fetch products from the platform."""
        pass
    
    @abstractmethod
    async def fetch_customers(
        self, 
        access_token: str, 
        shop_domain: str, 
        since: Optional[datetime] = None, 
        limit: int = 50
    ) -> List[Dict]:
        """Fetch customers from the platform."""
        pass
    
    @abstractmethod
    async def map_order_to_db_model(
        self, 
        platform_order_data: Dict, 
        store_id: uuid.UUID
    ) -> Dict:
        """Transform platform order data into our database model format."""
        pass
    
    @abstractmethod
    async def map_product_to_db_model(
        self, 
        platform_product_data: Dict, 
        store_id: uuid.UUID
    ) -> Dict:
        """Transform platform product data into our database model format."""
        pass
    
    @abstractmethod
    async def map_customer_to_db_model(
        self, 
        platform_customer_data: Dict, 
        store_id: uuid.UUID
    ) -> Dict:
        """Transform platform customer data into our database model format."""
        pass
    
    @abstractmethod
    async def get_api_client(self, access_token: str, shop_domain: str):
        """Get an instance of the platform's API client."""
        pass 
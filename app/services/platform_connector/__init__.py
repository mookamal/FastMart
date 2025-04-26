from typing import Dict
from .base import EcommercePlatformConnector
from .shopify import ShopifyConnector

# Dictionary to store connector instances
_connectors: Dict[str, EcommercePlatformConnector] = {
    'shopify': ShopifyConnector()
}

def get_connector(platform: str) -> EcommercePlatformConnector:
    """
    Get a connector instance for the specified platform.
    
    Args:
        platform: The platform name (e.g., 'shopify')
        
    Returns:
        An instance of EcommercePlatformConnector
        
    Raises:
        ValueError if the platform is not supported
    """
    connector = _connectors.get(platform.lower())
    if not connector:
        raise ValueError(f"Unsupported platform: {platform}")
    return connector 
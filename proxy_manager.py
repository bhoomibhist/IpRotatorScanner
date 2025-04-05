import random
import logging
import requests
import time
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ProxyManager:
    """
    Manages a list of proxy servers and rotates them for making requests.
    In demo mode, it will make direct requests without proxies.
    """
    
    def __init__(self, use_direct_connection=True):
        self.proxies = []
        self.current_index = 0
        self.last_update = 0
        self.use_direct_connection = use_direct_connection
        
        # Default free proxies for demo purposes - these are placeholders
        # In production, you'd use a paid proxy service or your own proxy list
        self.default_proxies = [
            'dummy-proxy-1',  # These are just placeholders
            'dummy-proxy-2',
            'dummy-proxy-3'
        ]
        
        # Load proxies on initialization
        self.update_proxies()
        
        if self.use_direct_connection:
            logger.info("Running in direct connection mode (no proxies)")
    
    def update_proxies(self) -> None:
        """
        Update the list of proxies. This method can fetch new proxies from
        a service or file, but for now it uses a default list.
        """
        # Don't update if it's been less than 1 hour since last update
        if time.time() - self.last_update < 3600:
            return
        
        try:
            # In a real implementation, you would fetch proxies from a service
            # Example:
            # response = requests.get('https://proxyservice.com/api/getproxies')
            # self.proxies = response.json()
            
            # For now, use default proxies
            self.proxies = self.default_proxies.copy()
            self.last_update = time.time()
            logger.info(f"Updated proxy list, found {len(self.proxies)} proxies")
        except Exception as e:
            logger.error(f"Error updating proxies: {str(e)}")
            # If update fails, keep using the existing list
            if not self.proxies:
                self.proxies = self.default_proxies.copy()
    
    def get_next_proxy(self) -> Dict[str, str]:
        """
        Returns the next proxy in the rotation, or empty dict for direct connection.
        """
        if self.use_direct_connection:
            # In direct connection mode, return empty dict (no proxy)
            return {}
            
        if not self.proxies:
            self.update_proxies()
        
        if not self.proxies:
            logger.warning("No proxies available")
            return {}
        
        # Rotate through proxies
        self.current_index = (self.current_index + 1) % len(self.proxies)
        proxy = self.proxies[self.current_index]
        
        # Format proxy for requests library
        proxy_dict = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        logger.debug(f"Using proxy: {proxy}")
        return proxy_dict
    
    def get_random_proxy(self) -> Dict[str, str]:
        """
        Returns a random proxy from the list, or empty dict for direct connection.
        """
        if self.use_direct_connection:
            # In direct connection mode, return empty dict (no proxy)
            return {}
            
        if not self.proxies:
            self.update_proxies()
        
        if not self.proxies:
            logger.warning("No proxies available")
            return {}
        
        proxy = random.choice(self.proxies)
        
        # Format proxy for requests library
        proxy_dict = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        logger.debug(f"Using random proxy: {proxy}")
        return proxy_dict
    
    def make_request(self, url: str, method: str = 'GET', max_retries: int = 3, 
                     timeout: int = 10, **kwargs) -> Optional[requests.Response]:
        """
        Makes a request using a rotating proxy or direct connection.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, etc.)
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object or None if all retries fail
        """
        retries = 0
        while retries < max_retries:
            # Get proxy configuration (empty dict for direct connection)
            proxy = self.get_next_proxy()
            
            try:
                if method.upper() == 'GET':
                    # If in direct connection mode, proxies will be empty dict
                    response = requests.get(
                        url, 
                        proxies=proxy if not self.use_direct_connection else None,
                        timeout=timeout,
                        **kwargs
                    )
                elif method.upper() == 'POST':
                    response = requests.post(
                        url,
                        proxies=proxy if not self.use_direct_connection else None,
                        timeout=timeout,
                        **kwargs
                    )
                else:
                    logger.error(f"Unsupported method: {method}")
                    return None
                
                if response.status_code < 400:
                    return response
                else:
                    logger.warning(f"Request failed with status {response.status_code}, retrying...")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed: {str(e)}, retrying...")
            
            retries += 1
            # Exponential backoff
            time.sleep(1)  # Reduced from 2**retries to be faster
        
        logger.error(f"Failed to make request to {url} after {max_retries} retries")
        return None

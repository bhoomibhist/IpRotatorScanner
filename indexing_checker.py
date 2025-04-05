import logging
import time
import re
import requests
from typing import Dict, List, Tuple
from urllib.parse import quote_plus
from proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

class IndexingChecker:
    """
    Checks if URLs are indexed on Google by making search requests.
    """
    
    def __init__(self, proxy_manager: ProxyManager = None):
        self.proxy_manager = proxy_manager or ProxyManager()
        self.search_url = "https://www.google.com/search"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        self.current_user_agent_index = 0
    
    def _get_next_user_agent(self) -> str:
        """Get the next user agent in rotation."""
        agent = self.user_agents[self.current_user_agent_index]
        self.current_user_agent_index = (self.current_user_agent_index + 1) % len(self.user_agents)
        return agent
    
    def is_url_indexed(self, url: str) -> bool:
        """
        Check if a URL is indexed on Google.
        
        Args:
            url: The URL to check
            
        Returns:
            True if the URL is indexed, False otherwise
        """
        # Construct a search query for the exact URL
        query = f'site:{url}'
        encoded_query = quote_plus(query)
        search_url = f"{self.search_url}?q={encoded_query}"
        
        headers = {
            'User-Agent': self._get_next_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Make the request using the proxy manager
        response = self.proxy_manager.make_request(search_url, headers=headers)
        
        if not response:
            logger.warning(f"Failed to check indexing for {url}")
            return False
        
        # Check if the URL appears in the search results
        # This is a simple check and might need refinement for production use
        return url.lower() in response.text.lower()
    
    def check_urls(self, urls: List[str]) -> Dict[str, bool]:
        """
        Check if multiple URLs are indexed on Google.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Dictionary mapping URLs to their indexing status
        """
        results = {}
        
        for url in urls:
            try:
                # Add scheme if missing
                if not url.startswith('http'):
                    url = 'https://' + url
                
                is_indexed = self.is_url_indexed(url)
                results[url] = is_indexed
                
                logger.info(f"URL {url} is {'indexed' if is_indexed else 'not indexed'}")
                
                # Sleep to avoid rate limiting
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error checking URL {url}: {str(e)}")
                results[url] = False
        
        return results

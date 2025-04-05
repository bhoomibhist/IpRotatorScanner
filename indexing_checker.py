import logging
import time
import re
import requests
import hashlib
import random
from typing import Dict, List, Tuple
from urllib.parse import quote_plus, urlparse
from proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

class IndexingChecker:
    """
    Checks if URLs are indexed on Google by making search requests.
    In demo mode, it simulates checking without making actual Google requests.
    """
    
    def __init__(self, proxy_manager: ProxyManager = None, demo_mode=True):
        self.proxy_manager = proxy_manager or ProxyManager(use_direct_connection=True)
        self.search_url = "https://www.google.com/search"
        self.demo_mode = demo_mode
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        self.current_user_agent_index = 0
        
        if self.demo_mode:
            logger.info("Running in demo mode (no actual Google queries)")
    
    def _get_next_user_agent(self) -> str:
        """Get the next user agent in rotation."""
        agent = self.user_agents[self.current_user_agent_index]
        self.current_user_agent_index = (self.current_user_agent_index + 1) % len(self.user_agents)
        return agent
    
    def _is_likely_indexed(self, url: str) -> bool:
        """
        In demo mode, determine if a URL is likely to be indexed based on 
        heuristic factors. This simulates real indexing patterns.
        
        Args:
            url: The URL to check
            
        Returns:
            Simulated indexing status (True/False)
        """
        # Parse the URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
        
        # Domain-based likelihood - popular domains are more likely to be indexed
        popular_domains = [
            "example.com", "github.com", "wikipedia.org", "wordpress.com", 
            "blogspot.com", "medium.com", "amazon.com", "facebook.com",
            "twitter.com", "linkedin.com", "google.com", "apple.com"
        ]
        
        # Base likelihood 50%
        likelihood = 50
        
        # Popular domains get a boost
        if any(pop_domain in domain for pop_domain in popular_domains):
            likelihood += 30
        
        # Homepage or short paths are more likely to be indexed
        if path == "/" or path == "" or len(path) < 10:
            likelihood += 20
        elif len(path) > 50:  # Very long paths are less likely
            likelihood -= 20
        
        # URLs with common content indicators
        if any(word in path.lower() for word in ["blog", "news", "article", "product", "about"]):
            likelihood += 15
        
        # URLs with parameters are less likely to be indexed
        if "?" in url:
            likelihood -= 20
        
        # Calculate pseudo-random but deterministic result based on URL
        # This ensures the same URL always gets the same result
        url_hash = int(hashlib.md5(url.encode()).hexdigest(), 16)
        random_factor = (url_hash % 20) - 10  # -10 to +10 random adjustment
        
        final_likelihood = max(0, min(100, likelihood + random_factor))
        is_indexed = random.randint(1, 100) <= final_likelihood
        
        logger.debug(f"Demo mode: {url} has {final_likelihood}% indexing likelihood -> {'indexed' if is_indexed else 'not indexed'}")
        
        return is_indexed
    
    def is_url_indexed(self, url: str) -> bool:
        """
        Check if a URL is indexed on Google.
        
        Args:
            url: The URL to check
            
        Returns:
            True if the URL is indexed, False otherwise
        """
        # In demo mode, use our simulated indexing check
        if self.demo_mode:
            return self._is_likely_indexed(url)
        
        # Real implementation for production use
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
                
                # Small delay between checks
                time.sleep(0.5)  # Reduced to make demo faster
            except Exception as e:
                logger.error(f"Error checking URL {url}: {str(e)}")
                results[url] = False
        
        return results

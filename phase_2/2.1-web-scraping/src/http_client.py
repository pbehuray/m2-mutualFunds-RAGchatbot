"""
HTTP Client Module
Handles HTTP requests with proper headers, rate limiting, and error handling.
"""

import requests
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class HTTPClient:
    """HTTP client with rate limiting and proper headers."""
    
    def __init__(
        self,
        base_headers: Optional[Dict[str, str]] = None,
        rate_limit_delay: float = 2.0,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize HTTP client.
        
        Args:
            base_headers: Default headers for all requests
            rate_limit_delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_headers = base_headers or self._get_default_headers()
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.last_request_time = 0
        self.session = requests.Session()
        
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Perform GET request with rate limiting and retry logic.
        
        Args:
            url: URL to fetch
            headers: Additional headers for this request
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails after retries
        """
        self._enforce_rate_limit()
        
        merged_headers = {**self.base_headers, **(headers or {})}
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    headers=merged_headers,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                # Exponential backoff
                wait_time = 2 ** attempt
                time.sleep(wait_time)
    
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """
        Perform POST request with rate limiting and retry logic.
        
        Args:
            url: URL to post to
            data: Form data
            json: JSON data
            headers: Additional headers for this request
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails after retries
        """
        self._enforce_rate_limit()
        
        merged_headers = {**self.base_headers, **(headers or {})}
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    url,
                    data=data,
                    json=json,
                    headers=merged_headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                # Exponential backoff
                wait_time = 2 ** attempt
                time.sleep(wait_time)
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Test the HTTP client
    with HTTPClient(rate_limit_delay=1.0) as client:
        test_url = "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
        
        if client.validate_url(test_url):
            print(f"Fetching: {test_url}")
            response = client.get(test_url)
            print(f"Status: {response.status_code}")
            print(f"Content length: {len(response.text)}")
        else:
            print("Invalid URL")

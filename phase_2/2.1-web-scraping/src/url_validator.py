"""
URL Validator Module
Validates URLs and checks accessibility.
"""

import requests
from urllib.parse import urlparse
from typing import Optional, Dict, Any
import logging


class URLValidator:
    """URL validator for checking URL validity and accessibility."""
    
    def __init__(self, timeout: int = 10, logger: Optional[logging.Logger] = None):
        """
        Initialize URL validator.
        
        Args:
            timeout: Request timeout in seconds
            logger: Logger instance
        """
        self.timeout = timeout
        self.logger = logger or self._get_default_logger()
    
    def _get_default_logger(self) -> logging.Logger:
        """Get default logger."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def validate_format(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL format is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([
                result.scheme in ['http', 'https'],
                result.netloc,
                len(result.netloc) > 0
            ])
        except Exception as e:
            self.logger.error(f"URL format validation failed for {url}: {str(e)}")
            return False
    
    def validate_accessibility(
        self,
        url: str,
        method: str = 'GET',
        expected_status: int = 200
    ) -> Dict[str, Any]:
        """
        Validate URL accessibility by making HTTP request.
        
        Args:
            url: URL to check
            method: HTTP method (GET, HEAD)
            expected_status: Expected HTTP status code
            
        Returns:
            Dictionary with validation results
        """
        if not self.validate_format(url):
            return {
                'accessible': False,
                'status_code': None,
                'error': 'Invalid URL format',
                'url': url
            }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            if method.upper() == 'HEAD':
                response = requests.head(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            else:
                response = requests.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            
            is_accessible = response.status_code == expected_status
            
            return {
                'accessible': is_accessible,
                'status_code': response.status_code,
                'error': None,
                'url': response.url,  # Final URL after redirects
                'redirects': len(response.history),
                'response_time': response.elapsed.total_seconds()
            }
            
        except requests.Timeout:
            return {
                'accessible': False,
                'status_code': None,
                'error': 'Request timeout',
                'url': url
            }
        except requests.ConnectionError:
            return {
                'accessible': False,
                'status_code': None,
                'error': 'Connection error',
                'url': url
            }
        except requests.RequestException as e:
            return {
                'accessible': False,
                'status_code': None,
                'error': str(e),
                'url': url
            }
        except Exception as e:
            return {
                'accessible': False,
                'status_code': None,
                'error': f"Unexpected error: {str(e)}",
                'url': url
            }
    
    def validate_multiple(
        self,
        urls: list,
        method: str = 'GET',
        expected_status: int = 200
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate multiple URLs.
        
        Args:
            urls: List of URLs to validate
            method: HTTP method (GET, HEAD)
            expected_status: Expected HTTP status code
            
        Returns:
            Dictionary mapping URLs to validation results
        """
        results = {}
        
        for url in urls:
            self.logger.info(f"Validating URL: {url}")
            results[url] = self.validate_accessibility(url, method, expected_status)
        
        return results
    
    def get_url_info(self, url: str) -> Dict[str, Any]:
        """
        Get detailed information about a URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary with URL information
        """
        parsed = urlparse(url)
        
        return {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'domain': parsed.netloc.split(':')[0] if parsed.netloc else None,
            'path': parsed.path,
            'params': parsed.params,
            'query': parsed.query,
            'fragment': parsed.fragment,
            'is_secure': parsed.scheme == 'https',
            'port': parsed.port if parsed.port else (443 if parsed.scheme == 'https' else 80)
        }
    
    def is_groww_url(self, url: str) -> bool:
        """
        Check if URL is from Groww platform.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is from Groww, False otherwise
        """
        parsed = urlparse(url)
        return 'groww.in' in parsed.netloc.lower()


if __name__ == "__main__":
    # Test the URL validator
    validator = URLValidator()
    
    # Test URL format validation
    test_urls = [
        "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        "invalid-url",
        "http://example.com",
        "ftp://example.com"
    ]
    
    print("Testing URL format validation:")
    for url in test_urls:
        is_valid = validator.validate_format(url)
        print(f"{url}: {'Valid' if is_valid else 'Invalid'}")
    
    # Test accessibility
    print("\nTesting accessibility validation:")
    test_url = "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    result = validator.validate_accessibility(test_url, method='HEAD')
    print(f"URL: {test_url}")
    print(f"Accessible: {result['accessible']}")
    print(f"Status Code: {result['status_code']}")
    print(f"Response Time: {result.get('response_time', 'N/A')}s")

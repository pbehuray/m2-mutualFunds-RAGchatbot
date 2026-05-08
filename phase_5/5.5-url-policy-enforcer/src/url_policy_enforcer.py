"""
URL Policy Enforcer Module
Enforces URL policy in responses.
"""

import re
from typing import List, Optional


class URLPolicyEnforcer:
    """Enforces URL policy."""
    
    def __init__(self, whitelisted_urls: List[str] = None):
        """
        Initialize URL policy enforcer.
        
        Args:
            whitelisted_urls: List of whitelisted URLs
        """
        self.whitelisted_urls = whitelisted_urls or []
    
    def count_urls(self, text: str) -> int:
        """
        Count URLs in text.
        
        Args:
            text: Input text
            
        Returns:
            Number of URLs found
        """
        url_pattern = re.compile(r'https?://\S+')
        urls = url_pattern.findall(text)
        return len(urls)
    
    def extract_urls(self, text: str) -> List[str]:
        """
        Extract URLs from text.
        
        Args:
            text: Input text
            
        Returns:
            List of URLs found
        """
        url_pattern = re.compile(r'https?://\S+')
        return url_pattern.findall(text)
    
    def is_url_whitelisted(self, url: str) -> bool:
        """
        Check if URL is whitelisted.
        
        Args:
            url: URL to check
            
        Returns:
            True if whitelisted, False otherwise
        """
        return url in self.whitelisted_urls
    
    def validate_url_count(
        self,
        text: str,
        expected_count: int
    ) -> bool:
        """
        Validate URL count matches expected.
        
        Args:
            text: Input text
            expected_count: Expected number of URLs
            
        Returns:
            True if valid, False otherwise
        """
        actual_count = self.count_urls(text)
        return actual_count == expected_count
    
    def validate_url_whitelist(self, text: str) -> bool:
        """
        Validate all URLs in text are whitelisted.
        
        Args:
            text: Input text
            
        Returns:
            True if all URLs whitelisted, False otherwise
        """
        urls = self.extract_urls(text)
        for url in urls:
            if not self.is_url_whitelisted(url):
                return False
        return True


if __name__ == "__main__":
    # Test URL policy enforcer
    enforcer = URLPolicyEnforcer(whitelisted_urls=['https://groww.in/funds'])
    
    test_texts = [
        "This is a response with no URLs",
        "Check https://groww.in/funds for more info",
        "Visit https://example.com and https://groww.in/funds"
    ]
    
    for text in test_texts:
        count = enforcer.count_urls(text)
        urls = enforcer.extract_urls(text)
        valid_zero = enforcer.validate_url_count(text, 0)
        valid_one = enforcer.validate_url_count(text, 1)
        whitelisted = enforcer.validate_url_whitelist(text)
        
        print(f"Text: {text}")
        print(f"  URL count: {count}")
        print(f"  URLs: {urls}")
        print(f"  Valid (0 URLs): {valid_zero}")
        print(f"  Valid (1 URL): {valid_one}")
        print(f"  All whitelisted: {whitelisted}")
        print()

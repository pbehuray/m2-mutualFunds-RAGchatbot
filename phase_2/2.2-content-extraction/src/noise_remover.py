"""
Noise Remover Module
Removes noise and irrelevant content from text.
"""

import re
from typing import List, Set


class NoiseRemover:
    """Noise remover for filtering out irrelevant content."""
    
    def __init__(self):
        """Initialize noise remover."""
        # Common navigation phrases
        self.navigation_phrases = [
            'skip to content',
            'navigation menu',
            'main menu',
            'search',
            'sign in',
            'sign up',
            'login',
            'register',
            'logout',
            'contact us',
            'about us',
            'privacy policy',
            'terms of service',
            'cookie policy',
            'copyright',
            'all rights reserved'
        ]
        
        # Common footer phrases
        self.footer_phrases = [
            'follow us on',
            'social media',
            'twitter',
            'facebook',
            'linkedin',
            'instagram',
            'youtube',
            'newsletter',
            'subscribe'
        ]
        
        # Common advertisement phrases
        self.ad_phrases = [
            'advertisement',
            'sponsored',
            'ad',
            'promo',
            'promotion',
            'click here',
            'buy now',
            'limited time offer',
            'special offer',
            'discount',
            'deal',
            'save up to'
        ]
    
    def remove_navigation_text(self, text: str) -> str:
        """
        Remove navigation-related text.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without navigation elements
        """
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            # Skip lines that are navigation phrases
            if not any(phrase in line_lower for phrase in self.navigation_phrases):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def remove_footer_text(self, text: str) -> str:
        """
        Remove footer-related text.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without footer elements
        """
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            # Skip lines that are footer phrases
            if not any(phrase in line_lower for phrase in self.footer_phrases):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def remove_advertisement_text(self, text: str) -> str:
        """
        Remove advertisement-related text.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without advertisement elements
        """
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            # Skip lines that are advertisement phrases
            if not any(phrase in line_lower for phrase in self.ad_phrases):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def remove_empty_lines(self, text: str, max_consecutive: int = 2) -> str:
        """
        Remove excessive empty lines.
        
        Args:
            text: Text to clean
            max_consecutive: Maximum consecutive empty lines allowed
            
        Returns:
            Text with normalized empty lines
        """
        lines = text.split('\n')
        filtered_lines = []
        empty_count = 0
        
        for line in lines:
            if not line.strip():
                empty_count += 1
                if empty_count <= max_consecutive:
                    filtered_lines.append(line)
            else:
                empty_count = 0
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def remove_short_lines(self, text: str, min_length: int = 3) -> str:
        """
        Remove very short lines that are likely noise.
        
        Args:
            text: Text to clean
            min_length: Minimum line length
            
        Returns:
            Text without short lines
        """
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            if len(line.strip()) >= min_length or not line.strip():
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def remove_duplicate_lines(self, text: str) -> str:
        """
        Remove duplicate consecutive lines.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without duplicate consecutive lines
        """
        lines = text.split('\n')
        filtered_lines = []
        
        prev_line = None
        for line in lines:
            if line != prev_line:
                filtered_lines.append(line)
                prev_line = line
        
        return '\n'.join(filtered_lines)
    
    def remove_numbers_only(self, text: str) -> str:
        """
        Remove lines that contain only numbers.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without number-only lines
        """
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            if not line.strip().isdigit():
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def remove_noise(self, text: str) -> str:
        """
        Apply all noise removal techniques.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        text = self.remove_navigation_text(text)
        text = self.remove_footer_text(text)
        text = self.remove_advertisement_text(text)
        text = self.remove_empty_lines(text)
        text = self.remove_short_lines(text)
        text = self.remove_duplicate_lines(text)
        text = self.remove_numbers_only(text)
        
        return text.strip()


if __name__ == "__main__":
    # Test the noise remover
    remover = NoiseRemover()
    
    test_text = """
    Skip to content
    Main menu
    Sign in
    Contact us
    
    This is the main content of the document.
    It contains important information.
    
    Follow us on Twitter
    Social media
    Newsletter
    Subscribe
    
    This is more content.
    This is more content.
    
    Advertisement
    Sponsored
    Buy now
    """
    
    print("Original text:")
    print(test_text)
    print("\nCleaned text:")
    cleaned = remover.remove_noise(test_text)
    print(cleaned)

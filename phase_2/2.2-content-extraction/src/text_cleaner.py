"""
Text Cleaner Module
Cleans and normalizes text from scraped documents.
"""

import re
from typing import Optional, List


class TextCleaner:
    """Text cleaner for normalizing and cleaning extracted text."""
    
    def __init__(self):
        """Initialize text cleaner."""
        pass
    
    def clean(self, text: str) -> str:
        """
        Clean text by removing noise and normalizing.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = self._remove_extra_whitespace(text)
        
        # Remove special characters but keep basic punctuation
        text = self._remove_special_characters(text)
        
        # Remove multiple punctuation
        text = self._remove_multiple_punctuation(text)
        
        # Normalize quotes
        text = self._normalize_quotes(text)
        
        # Remove control characters
        text = self._remove_control_characters(text)
        
        return text.strip()
    
    def _remove_extra_whitespace(self, text: str) -> str:
        """
        Remove extra whitespace.
        
        Args:
            text: Text to clean
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        
        return '\n'.join(lines)
    
    def _remove_special_characters(self, text: str) -> str:
        """
        Remove special characters but keep basic punctuation.
        
        Args:
            text: Text to clean
            
        Returns:
            Text with special characters removed
        """
        # Keep alphanumeric, spaces, and basic punctuation
        # . , : ; ( ) [ ] { } % $ ₹ ? ! -
        pattern = r'[^\w\s\.\,\:\;\(\)\[\]\{\}\%\$\₹\?\!\-]'
        text = re.sub(pattern, '', text)
        
        return text
    
    def _remove_multiple_punctuation(self, text: str) -> str:
        """
        Remove multiple consecutive punctuation marks.
        
        Args:
            text: Text to clean
            
        Returns:
            Text with single punctuation marks
        """
        # Replace multiple periods with single period
        text = re.sub(r'\.{2,}', '.', text)
        
        # Replace multiple commas with single comma
        text = re.sub(r'\,{2,}', ',', text)
        
        # Replace multiple colons with single colon
        text = re.sub(r'\:{2,}', ':', text)
        
        # Replace multiple semicolons with single semicolon
        text = re.sub(r'\;{2,}', ';', text)
        
        return text
    
    def _normalize_quotes(self, text: str) -> str:
        """
        Normalize different quote types to standard quotes.
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized quotes
        """
        # Replace curly quotes with straight quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('`', "'")
        
        return text
    
    def _remove_control_characters(self, text: str) -> str:
        """
        Remove control characters.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without control characters
        """
        # Remove control characters except newline and tab
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    def remove_urls(self, text: str) -> str:
        """
        Remove URLs from text.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without URLs
        """
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(url_pattern, '', text)
        
        return text
    
    def remove_emails(self, text: str) -> str:
        """
        Remove email addresses from text.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without email addresses
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, '', text)
        
        return text
    
    def remove_phone_numbers(self, text: str) -> str:
        """
        Remove phone numbers from text.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without phone numbers
        """
        # Remove common phone number formats
        phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        text = re.sub(phone_pattern, '', text)
        
        return text
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text.
        
        Args:
            text: Text to extract sentences from
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting on period, exclamation, question mark
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def truncate_to_length(self, text: str, max_length: int, ellipsis: str = "...") -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            ellipsis: Ellipsis string to add if truncated
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length - len(ellipsis)]
        return truncated + ellipsis


if __name__ == "__main__":
    # Test the text cleaner
    cleaner = TextCleaner()
    
    test_text = """
    This is a  test   text with    extra    whitespace.
    
    It has "curly quotes" and 'single quotes'.
    
    Special characters: @#$%^&*()_+ should be removed... but keep .,:;()-[]
    
    Multiple newlines
    
    
    should be reduced.
    """
    
    print("Original text:")
    print(test_text)
    print("\nCleaned text:")
    cleaned = cleaner.clean(test_text)
    print(cleaned)

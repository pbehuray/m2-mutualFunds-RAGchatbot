"""
PII Detection Module
Detects personally identifiable information in user messages.
"""

import re
from typing import List, Tuple, Optional


class PIIDetector:
    """Detects PII in text."""
    
    def __init__(self):
        """Initialize PII detector with regex patterns."""
        # PAN (Permanent Account Number) - 10 alphanumeric characters
        self.pan_pattern = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', re.IGNORECASE)
        
        # Aadhaar - 12 digits
        self.aadhaar_pattern = re.compile(r'\b\d{12}\b')
        
        # Email
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Phone (Indian) - 10 digits
        self.phone_pattern = re.compile(r'\b[6-9]\d{9}\b')
        
        # OTP - typically 4-6 digits
        self.otp_pattern = re.compile(r'\b\d{4,6}\b')
    
    def detect_pii(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detect PII in text.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (has_pii, detected_types)
        """
        detected_types = []
        
        if self.pan_pattern.search(text):
            detected_types.append('PAN')
        
        if self.aadhaar_pattern.search(text):
            detected_types.append('Aadhaar')
        
        if self.email_pattern.search(text):
            detected_types.append('Email')
        
        if self.phone_pattern.search(text):
            detected_types.append('Phone')
        
        if self.otp_pattern.search(text):
            detected_types.append('OTP')
        
        has_pii = len(detected_types) > 0
        
        return has_pii, detected_types
    
    def mask_pii(self, text: str) -> str:
        """
        Mask PII in text for logging.
        
        Args:
            text: Input text
            
        Returns:
            Text with PII masked
        """
        text = self.pan_pattern.sub('[PAN]', text)
        text = self.aadhaar_pattern.sub('[AADHAAR]', text)
        text = self.email_pattern.sub('[EMAIL]', text)
        text = self.phone_pattern.sub('[PHONE]', text)
        text = self.otp_pattern.sub('[OTP]', text)
        
        return text


if __name__ == "__main__":
    # Test PII detector
    detector = PIIDetector()
    
    test_queries = [
        "What is the expense ratio?",
        "My PAN is ABCDE1234F, what should I invest?",
        "Email me at test@example.com for details",
        "Call me at 9876543210",
        "My OTP is 123456"
    ]
    
    for query in test_queries:
        has_pii, types = detector.detect_pii(query)
        print(f"Query: {query}")
        print(f"  Has PII: {has_pii}")
        print(f"  Types: {types}")
        print(f"  Masked: {detector.mask_pii(query)}")
        print()

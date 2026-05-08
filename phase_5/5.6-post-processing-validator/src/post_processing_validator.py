"""
Post-Processing Validator Module
Validates generated responses against hard checks.
"""

import re
from typing import Dict, Any, List


class PostProcessingValidator:
    """Validates generated responses."""
    
    def __init__(self):
        """Initialize validator with banned tokens."""
        self.banned_tokens = [
            'recommend', 'should invest', 'better than', 'will outperform',
            'good investment', 'bad investment', 'advice', 'suggestion'
        ]
    
    def check_sentence_count(self, text: str, max_sentences: int = 3) -> bool:
        """
        Check sentence count (body only, before Source/Last updated lines).
        Counts only lines ending with sentence-terminating punctuation.
        """
        lines = text.split('\n')
        body_lines = [
            l for l in lines
            if not l.startswith('Source:') and not l.startswith('Last updated')
        ]
        body = ' '.join(body_lines)
        # Split on sentence-ending punctuation followed by whitespace or end
        sentences = re.split(r'(?<=[.!?])\s+', body)
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences) <= max_sentences
    
    def check_banned_tokens(self, text: str) -> bool:
        """
        Check for banned tokens.
        
        Args:
            text: Input text
            
        Returns:
            True if no banned tokens found, False otherwise
        """
        text_lower = text.lower()
        for token in self.banned_tokens:
            if token in text_lower:
                return False
        return True
    
    def check_footer_present(self, text: str) -> bool:
        """
        Check if footer is present.
        
        Args:
            text: Input text
            
        Returns:
            True if footer present, False otherwise
        """
        return 'Last updated from sources:' in text
    
    def validate(self, response: str, require_url: bool = False) -> Dict[str, Any]:
        """
        Validate response against all checks.

        Args:
            response:    Generated response
            require_url: Whether URL is required

        Returns:
            Dictionary with validation results
        """
        checks = {
            'sentence_count_valid': self.check_sentence_count(response, max_sentences=8),
            'no_banned_tokens':     self.check_banned_tokens(response),
            'footer_present':       self.check_footer_present(response),
        }

        # URL count check
        url_count = len(re.findall(r'https?://\S+', response))
        if require_url:
            checks['url_count_valid'] = url_count >= 1
        else:
            checks['url_count_valid'] = url_count == 0

        checks['all_valid'] = all(checks.values())
        return checks


if __name__ == "__main__":
    # Test post-processing validator
    validator = PostProcessingValidator()
    
    test_responses = [
        "This is a valid answer. It has two sentences. Source: https://test.com\nLast updated from sources: 2024-01-01",
        "I recommend you invest in this fund. It's great.",
        "This answer has way too many sentences and continues on and on and on and on and on and on."
    ]
    
    for response in test_responses:
        validation = validator.validate(response, require_url=True)
        print(f"Response: {response[:100]}...")
        print(f"  Validation: {validation}")
        print()

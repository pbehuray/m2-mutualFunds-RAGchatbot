"""
Boilerplate Remover Module
Removes boilerplate content from documents.
"""

from bs4 import BeautifulSoup
from typing import List, Set
import re


class BoilerplateRemover:
    """Boilerplate remover for eliminating template/repetitive content."""
    
    def __init__(self):
        """Initialize boilerplate remover."""
        # CSS selectors for common boilerplate elements
        self.boilerplate_selectors = [
            'nav', 'navigation', 'navbar', 'menu',
            'footer', 'site-footer',
            'header', 'site-header',
            'aside', 'sidebar',
            '.advertisement', '.ad', '.ads',
            '.social-share', '.share-buttons',
            '.comments', '.comment-section',
            '.related-posts', '.similar-posts',
            '.breadcrumbs',
            '.pagination',
            '.cookie-notice', '.cookie-banner',
            '.popup', '.modal',
            'script', 'style', 'noscript'
        ]
        
        # Common boilerplate patterns
        self.boilerplate_patterns = [
            r'© \d{4}.*?rights reserved',
            r'all rights reserved',
            r'privacy policy',
            r'terms of service',
            r'cookie policy',
            r'follow us on',
            r'subscribe to our',
            r'sign up for our',
            r'powered by',
            r'designed by'
        ]
    
    def remove_from_html(self, html: str) -> str:
        """
        Remove boilerplate from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            HTML with boilerplate removed
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove boilerplate elements
        for selector in self.boilerplate_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        return str(soup)
    
    def remove_from_text(self, text: str) -> str:
        """
        Remove boilerplate patterns from text.
        
        Args:
            text: Text content
            
        Returns:
            Text with boilerplate removed
        """
        for pattern in self.boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def remove_repetitive_phrases(self, text: str, min_occurrences: int = 3) -> str:
        """
        Remove phrases that repeat frequently (likely boilerplate).
        
        Args:
            text: Text to clean
            min_occurrences: Minimum occurrences to consider as boilerplate
            
        Returns:
            Text with repetitive phrases removed
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Count sentence occurrences
        sentence_counts = {}
        for sentence in sentences:
            sentence_lower = sentence.lower()
            sentence_counts[sentence_lower] = sentence_counts.get(sentence_lower, 0) + 1
        
        # Identify boilerplate sentences
        boilerplate_sentences = {
            sentence for sentence, count in sentence_counts.items()
            if count >= min_occurrences and len(sentence.split()) > 3
        }
        
        # Remove boilerplate sentences
        filtered_sentences = [
            sentence for sentence in sentences
            if sentence.lower() not in boilerplate_sentences
        ]
        
        return '. '.join(filtered_sentences)
    
    def remove_template_placeholders(self, text: str) -> str:
        """
        Remove template placeholders.
        
        Args:
            text: Text to clean
            
        Returns:
            Text without placeholders
        """
        # Remove common placeholder patterns
        patterns = [
            r'\{.*?\}',  # {placeholder}
            r'\[.*?\]',  # [placeholder]
            r'{{.*?}}',  # {{placeholder}}
            r'\[\[.*?\]\]',  # [[placeholder]]
            r'<!--.*?-->',  # HTML comments
            r'%\{.*?\}',  # %{placeholder}
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        
        return text
    
    def remove_boilerplate(self, text: str, is_html: bool = False) -> str:
        """
        Apply all boilerplate removal techniques.
        
        Args:
            text: Content to clean
            is_html: Whether content is HTML
            
        Returns:
            Cleaned content
        """
        if is_html:
            text = self.remove_from_html(text)
            # Extract text after removing HTML boilerplate
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
        
        text = self.remove_from_text(text)
        text = self.remove_repetitive_phrases(text)
        text = self.remove_template_placeholders(text)
        
        return text.strip()


if __name__ == "__main__":
    # Test the boilerplate remover
    remover = BoilerplateRemover()
    
    test_html = """
    <html>
        <nav>Navigation Menu</nav>
        <div class="content">
            <h1>Main Content</h1>
            <p>This is the main content.</p>
        </div>
        <footer>© 2024 All Rights Reserved. Privacy Policy. Terms of Service.</footer>
        <script>console.log('test');</script>
    </html>
    """
    
    print("Original HTML:")
    print(test_html)
    print("\nCleaned HTML:")
    cleaned = remover.remove_boilerplate(test_html, is_html=True)
    print(cleaned)

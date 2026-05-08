"""
HTML Parser Module
Extracts content from HTML pages using BeautifulSoup.
"""

from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Any
import re


class HTMLParser:
    """HTML parser for extracting clean content from web pages."""
    
    def __init__(self):
        """Initialize HTML parser."""
        self.boilerplate_selectors = [
            'nav', 'footer', 'header', 'aside',
            '.advertisement', '.ads', '.sidebar',
            '.navigation', '.menu', '.footer-links',
            'script', 'style', 'noscript'
        ]
        
    def parse(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content.
        
        Args:
            html_content: Raw HTML string
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, 'html.parser')
    
    def extract_text(self, soup: BeautifulSoup, remove_boilerplate: bool = True) -> str:
        """
        Extract clean text from HTML.
        
        Args:
            soup: BeautifulSoup object
            remove_boilerplate: Whether to remove boilerplate elements
            
        Returns:
            Cleaned text content
        """
        if remove_boilerplate:
            soup = self._remove_boilerplate(soup)
        
        # Get text and clean it
        text = soup.get_text(separator=' ', strip=True)
        text = self._clean_text(text)
        
        return text
    
    def _remove_boilerplate(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Remove boilerplate elements from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            BeautifulSoup object with boilerplate removed
        """
        for selector in self.boilerplate_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        return soup
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\-\:\;\(\)\[\]\{\}\%\$\₹]', '', text)
        
        # Remove multiple periods
        text = re.sub(r'\.{2,}', '.', text)
        
        return text.strip()
    
    def extract_links(self, soup: BeautifulSoup, base_url: str = None) -> List[Dict[str, str]]:
        """
        Extract all links from HTML.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of dictionaries with link information
        """
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text(strip=True)
            
            # Resolve relative URLs if base_url provided
            if base_url and not href.startswith('http'):
                href = f"{base_url.rstrip('/')}/{href.lstrip('/')}"
            
            links.append({
                'url': href,
                'text': text
            })
        
        return links
    
    def extract_tables(self, soup: BeautifulSoup) -> List[List[List[str]]]:
        """
        Extract tables from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of tables (each table is a list of rows, each row is a list of cells)
        """
        tables = []
        
        for table in soup.find_all('table'):
            table_data = []
            
            for row in table.find_all('tr'):
                row_data = []
                
                for cell in row.find_all(['td', 'th']):
                    cell_text = cell.get_text(strip=True)
                    row_data.append(cell_text)
                
                if row_data:
                    table_data.append(row_data)
            
            if table_data:
                tables.append(table_data)
        
        return tables
    
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract metadata from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['description'] = meta_desc.get('content', '')
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata['keywords'] = meta_keywords.get('content', '')
        
        # Open Graph tags
        og_tags = {}
        for meta in soup.find_all('meta', property=lambda x: x and x.startswith('og:')):
            og_tags[meta['property']] = meta.get('content', '')
        if og_tags:
            metadata['open_graph'] = og_tags
        
        return metadata
    
    def extract_by_selector(self, soup: BeautifulSoup, selector: str) -> List[str]:
        """
        Extract text using CSS selector.
        
        Args:
            soup: BeautifulSoup object
            selector: CSS selector
            
        Returns:
            List of text content from matching elements
        """
        elements = soup.select(selector)
        return [elem.get_text(strip=True) for elem in elements if elem.get_text(strip=True)]


if __name__ == "__main__":
    # Test the HTML parser
    parser = HTMLParser()
    
    test_html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <nav>Navigation</nav>
            <h1>Main Content</h1>
            <p>This is the main content.</p>
            <table>
                <tr><th>Header 1</th><th>Header 2</th></tr>
                <tr><td>Data 1</td><td>Data 2</td></tr>
            </table>
            <footer>Footer</footer>
        </body>
    </html>
    """
    
    soup = parser.parse(test_html)
    text = parser.extract_text(soup)
    metadata = parser.extract_metadata(soup)
    tables = parser.extract_tables(soup)
    
    print("Extracted Text:", text)
    print("Metadata:", metadata)
    print("Tables:", tables)

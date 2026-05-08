"""
Document Structure Preserver Module
Preserves document structure during text extraction.
"""

from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any
import re


class DocumentStructurePreserver:
    """Preserves document structure during text extraction."""
    
    def __init__(self):
        """Initialize document structure preserver."""
        pass
    
    def extract_structure(self, html: str) -> Dict[str, Any]:
        """
        Extract document structure from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Dictionary with document structure
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        structure = {
            'headings': self._extract_headings(soup),
            'lists': self._extract_lists(soup),
            'tables': self._extract_tables_structure(soup),
            'paragraphs': self._extract_paragraphs(soup)
        }
        
        return structure
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract headings with hierarchy.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of heading dictionaries
        """
        headings = []
        
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                headings.append({
                    'level': level,
                    'text': heading.get_text(strip=True),
                    'tag': f'h{level}'
                })
        
        return headings
    
    def _extract_lists(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract lists with items.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of list dictionaries
        """
        lists = []
        
        for list_tag in soup.find_all(['ul', 'ol']):
            list_type = list_tag.name  # 'ul' or 'ol'
            items = [li.get_text(strip=True) for li in list_tag.find_all('li')]
            
            lists.append({
                'type': list_type,
                'items': items
            })
        
        return lists
    
    def _extract_tables_structure(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract table structure.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of table dictionaries
        """
        tables = []
        
        for table in soup.find_all('table'):
            # Extract headers
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
            
            # Extract rows
            rows = []
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            
            tables.append({
                'headers': headers,
                'rows': rows
            })
        
        return tables
    
    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract paragraphs.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of paragraph texts
        """
        paragraphs = []
        
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)
        
        return paragraphs
    
    def format_text_with_structure(self, structure: Dict[str, Any]) -> str:
        """
        Format text with preserved structure.
        
        Args:
            structure: Document structure dictionary
            
        Returns:
            Formatted text
        """
        formatted = []
        
        # Add headings
        for heading in structure['headings']:
            prefix = '#' * heading['level']
            formatted.append(f"{prefix} {heading['text']}")
        
        # Add paragraphs
        for paragraph in structure['paragraphs']:
            formatted.append(paragraph)
        
        # Add lists
        for lst in structure['lists']:
            for item in lst['items']:
                marker = '-' if lst['type'] == 'ul' else '1.'
                formatted.append(f"{marker} {item}")
        
        # Add tables
        for table in structure['tables']:
            if table['headers']:
                formatted.append(' | '.join(table['headers']))
            for row in table['rows']:
                formatted.append(' | '.join(row))
        
        return '\n\n'.join(formatted)
    
    def preserve_section_hierarchy(self, text: str) -> str:
        """
        Preserve section hierarchy in text.
        
        Args:
            text: Text content
            
        Returns:
            Text with preserved hierarchy
        """
        # Add section markers based on patterns
        lines = text.split('\n')
        preserved_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Detect potential headings (short, capitalized, or ending with colon)
            if stripped and len(stripped) < 100 and not stripped.endswith('.'):
                if (stripped.isupper() or 
                    stripped.istitle() or 
                    stripped.endswith(':')):
                    # Add heading marker
                    if not stripped.startswith('#'):
                        line = f"## {line}"
            
            preserved_lines.append(line)
        
        return '\n'.join(preserved_lines)


if __name__ == "__main__":
    # Test the document structure preserver
    preserver = DocumentStructurePreserver()
    
    test_html = """
    <html>
        <body>
            <h1>Main Title</h1>
            <p>This is a paragraph.</p>
            <h2>Section 1</h2>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <h2>Section 2</h2>
            <table>
                <tr><th>Header 1</th><th>Header 2</th></tr>
                <tr><td>Data 1</td><td>Data 2</td></tr>
            </table>
        </body>
    </html>
    """
    
    print("Extracting structure...")
    structure = preserver.extract_structure(test_html)
    print("Structure:", structure)
    
    print("\nFormatted text:")
    formatted = preserver.format_text_with_structure(structure)
    print(formatted)

"""
Source Attribution Module
Handles source tracking and citation formatting.
"""

from typing import Dict, Any


class SourceAttributor:
    """Manages source attribution for retrieved chunks."""
    
    def format_citation(self, chunk: Dict[str, Any]) -> str:
        """
        Format citation for a chunk.
        
        Args:
            chunk: Chunk dictionary with metadata
            
        Returns:
            Formatted citation string
        """
        metadata = chunk.get('metadata', {})
        source_file = metadata.get('source_file', 'Unknown source')
        chunk_id = metadata.get('chunk_id', 'Unknown chunk')
        scheme_name = metadata.get('scheme_name', 'Unknown scheme')
        
        citation = f"Source: {source_file} | Chunk: {chunk_id} | Scheme: {scheme_name}"
        
        return citation
    
    def extract_source_url(self, chunk: Dict[str, Any]) -> str:
        """
        Extract source URL from chunk metadata.
        
        Args:
            chunk: Chunk dictionary with metadata
            
        Returns:
            Source URL or file path
        """
        metadata = chunk.get('metadata', {})
        return metadata.get('source_file', metadata.get('source_url', 'Unknown'))
    
    def get_scheme_name(self, chunk: Dict[str, Any]) -> str:
        """
        Get scheme name from chunk.
        
        Args:
            chunk: Chunk dictionary with metadata
            
        Returns:
            Scheme name
        """
        metadata = chunk.get('metadata', {})
        return metadata.get('scheme_name', 'Unknown scheme')
    
    def format_result_with_citation(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format result with citation.
        
        Args:
            chunk: Chunk dictionary
            
        Returns:
            Formatted result with citation
        """
        return {
            'text': chunk['text'],
            'similarity_score': chunk.get('similarity_score', 0),
            'citation': self.format_citation(chunk),
            'source_url': self.extract_source_url(chunk),
            'scheme_name': self.get_scheme_name(chunk),
            'chunk_id': chunk.get('metadata', {}).get('chunk_id', 'Unknown')
        }


if __name__ == "__main__":
    # Test source attributor
    attributor = SourceAttributor()
    
    test_chunk = {
        'text': 'HDFC Equity Fund has an expense ratio of 1.04%',
        'similarity_score': 0.85,
        'metadata': {
            'source_file': 'hdfc_equity_fund_direct_growth.html',
            'chunk_id': 'hdfc_equity_fund_subsection_0',
            'scheme_name': 'Hdfc Equity Fund Direct Growth'
        }
    }
    
    result = attributor.format_result_with_citation(test_chunk)
    
    print("Formatted result:")
    print(f"  Text: {result['text']}")
    print(f"  Similarity: {result['similarity_score']}")
    print(f"  Citation: {result['citation']}")
    print(f"  Source URL: {result['source_url']}")
    print(f"  Scheme: {result['scheme_name']}")

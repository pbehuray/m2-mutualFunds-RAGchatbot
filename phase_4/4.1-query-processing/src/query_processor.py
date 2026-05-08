"""
Query Processor Module
Processes user queries for effective retrieval.
"""

from typing import List, Dict, Any
import re
import string

# Import embedding generator
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'phase_3', '3.3-embedding-generation', 'src'))
from embedding_generator import EmbeddingGenerator


class QueryProcessor:
    """Process user queries for retrieval."""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize query processor.
        
        Args:
            model_name: Name of the embedding model
        """
        self.embedding_generator = EmbeddingGenerator(model_name)
    
    def normalize_query(self, query: str) -> str:
        """
        Normalize query text.
        
        Args:
            query: Raw query string
            
        Returns:
            Normalized query string
        """
        # Convert to lowercase
        query = query.lower()
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Remove special characters (keep alphanumeric, spaces, basic punctuation)
        query = re.sub(r'[^\w\s\.\,\?\!]', '', query)
        
        return query.strip()
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process query and generate embedding.
        
        Args:
            query: Raw query string
            
        Returns:
            Dictionary with processed query and embedding
        """
        normalized_query = self.normalize_query(query)
        embedding = self.embedding_generator.generate_embedding(normalized_query)
        
        return {
            'original_query': query,
            'normalized_query': normalized_query,
            'embedding': embedding
        }
    
    def filter_by_scheme(self, query: str, available_schemes: List[str]) -> str:
        """
        Check if query mentions a specific scheme name.
        
        Args:
            query: Query string
            available_schemes: List of available scheme names
            
        Returns:
            Scheme name if found, None otherwise
        """
        query_lower = query.lower()
        
        for scheme in available_schemes:
            scheme_lower = scheme.lower()
            # Check if scheme name appears in query
            if scheme_lower in query_lower:
                return scheme
        
        return None


if __name__ == "__main__":
    # Test query processor
    processor = QueryProcessor()
    
    test_query = "What is the expense ratio of HDFC Equity Fund?"
    result = processor.process_query(test_query)
    
    print(f"Original query: {result['original_query']}")
    print(f"Normalized query: {result['normalized_query']}")
    print(f"Embedding dimension: {len(result['embedding'])}")

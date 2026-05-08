"""
Retrieval Pipeline
End-to-end retrieval system combining query processing, search, and source attribution.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '4.1-query-processing', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '4.2-similarity-search', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '4.3-source-attribution', 'src'))

from query_processor import QueryProcessor
from retriever import Retriever
from source_attributor import SourceAttributor


class RetrievalPipeline:
    """End-to-end retrieval pipeline."""
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize retrieval pipeline.
        
        Args:
            persist_directory: Directory for vector database
        """
        self.query_processor = QueryProcessor()
        self.retriever = Retriever(persist_directory=persist_directory)
        self.source_attributor = SourceAttributor()
    
    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        scheme_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query
            n_results: Number of results to return
            scheme_filter: Optional scheme name filter
            
        Returns:
            Dictionary with query info and retrieved results
        """
        # Process query
        query_info = self.query_processor.process_query(query)
        
        # Check if query mentions a specific scheme
        available_schemes = self.retriever.get_available_schemes()
        detected_scheme = self.query_processor.filter_by_scheme(query, available_schemes)
        
        # Use detected scheme if no explicit filter provided
        if scheme_filter is None and detected_scheme:
            scheme_filter = detected_scheme
        
        # Search
        results = self.retriever.search(
            query=query_info['normalized_query'],
            n_results=n_results,
            scheme_filter=scheme_filter
        )
        
        # Format results with citations
        formatted_results = []
        for result in results:
            formatted_result = self.source_attributor.format_result_with_citation(result)
            formatted_results.append(formatted_result)
        
        return {
            'query': query_info['original_query'],
            'normalized_query': query_info['normalized_query'],
            'scheme_filter': scheme_filter,
            'detected_scheme': detected_scheme,
            'num_results': len(formatted_results),
            'results': formatted_results
        }


def main():
    """Main function to test the retrieval pipeline."""
    # Define paths
    base_dir = Path(__file__).parent.parent
    persist_directory = str(base_dir / 'phase-3' / 'vector_db')
    
    print("=" * 60)
    print("Retrieval Pipeline Test")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = RetrievalPipeline(persist_directory=persist_directory)
    
    # Test queries
    test_queries = [
        "What is the expense ratio?",
        "HDFC Equity Fund returns",
        "Top holdings in the fund"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = pipeline.retrieve(query, n_results=3)
        
        print(f"Normalized query: {result['normalized_query']}")
        print(f"Scheme filter: {result['scheme_filter']}")
        print(f"Detected scheme: {result['detected_scheme']}")
        print(f"Results found: {result['num_results']}")
        
        for i, res in enumerate(result['results']):
            print(f"\nResult {i+1}:")
            print(f"  Similarity: {res['similarity_score']:.4f}")
            print(f"  Scheme: {res['scheme_name']}")
            print(f"  Text: {res['text'][:150]}...")
            print(f"  Citation: {res['citation']}")


if __name__ == "__main__":
    main()

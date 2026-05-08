"""
Retrieval Module
Performs similarity search on vector database.
"""

from typing import List, Dict, Any, Optional
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'phase_3', '3.2-vector-database-setup', 'src'))
from vector_store import VectorStore
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'phase_3', '3.3-embedding-generation', 'src'))
from embedding_generator import EmbeddingGenerator


class Retriever:
    """Retrieval system using vector database."""
    
    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = "mutual_fund_chunks"
    ):
        """
        Initialize retriever.
        
        Args:
            persist_directory: Directory for vector database
            collection_name: Name of the collection
        """
        self.vector_store = VectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        self.embedding_generator = EmbeddingGenerator()
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        scheme_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks.
        
        Args:
            query: Query string
            n_results: Number of results to return
            scheme_filter: Optional scheme name to filter by
            
        Returns:
            List of retrieved chunks with metadata and scores
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Build metadata filter if scheme specified
        where_filter = None
        if scheme_filter:
            where_filter = {"scheme_name": scheme_filter}
        
        # Search vector database
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results,
            where=where_filter
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, (doc_id, document, metadata, distance) in enumerate(zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convert distance to similarity score (cosine)
                similarity = 1 - distance
                
                formatted_results.append({
                    'chunk_id': doc_id,
                    'text': document,
                    'metadata': metadata,
                    'similarity_score': similarity,
                    'distance': distance
                })
        
        return formatted_results
    
    def get_available_schemes(self) -> List[str]:
        """
        Get list of available scheme names.
        
        Returns:
            List of unique scheme names
        """
        results = self.vector_store.collection.get()
        schemes = set()
        
        for metadata in results['metadatas']:
            if 'scheme_name' in metadata:
                schemes.add(metadata['scheme_name'])
        
        return list(schemes)


if __name__ == "__main__":
    # Test retriever
    retriever = Retriever(persist_directory="../../../phase-3/vector_db")
    
    print("Available schemes:", retriever.get_available_schemes())
    
    test_query = "What is the expense ratio?"
    results = retriever.search(test_query, n_results=3)
    
    print(f"\nQuery: {test_query}")
    print(f"Results: {len(results)}")
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Similarity: {result['similarity_score']:.4f}")
        print(f"  Scheme: {result['metadata'].get('scheme_name', 'N/A')}")
        print(f"  Text: {result['text'][:100]}...")

"""
Vector Store Module
Manages vector database operations using ChromaDB.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import json
from pathlib import Path


class VectorStore:
    """Vector store manager using ChromaDB."""
    
    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = "mutual_fund_chunks"
    ):
        """
        Initialize vector store.
        
        Args:
            persist_directory: Directory to persist vector database
            collection_name: Name of the collection
        """
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        if persist_directory:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ):
        """
        Add chunks with embeddings to the vector store.
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
            embeddings: List of embedding vectors
        """
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            chunk_id = chunk.get('metadata', {}).get('chunk_id', str(hash(chunk['text'])))
            ids.append(chunk_id)
            documents.append(chunk['text'])
            
            # Flatten metadata for ChromaDB
            metadata = {}
            for key, value in chunk.get('metadata', {}).items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value
                elif isinstance(value, dict):
                    # Skip nested dicts for now
                    continue
                else:
                    metadata[key] = str(value)
            
            metadatas.append(metadata)
        
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Dict[str, Any] = None,
        where_document: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter
            
        Returns:
            Query results
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        
        return results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Dictionary with collection stats
        """
        count = self.collection.count()
        
        return {
            'collection_name': self.collection_name,
            'count': count,
            'metadata': self.collection.metadata
        }
    
    def delete_collection(self):
        """Delete the collection."""
        self.client.delete_collection(self.collection_name)
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        # Delete and recreate
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )


if __name__ == "__main__":
    # Test the vector store
    store = VectorStore(persist_directory="./test_db")
    
    print("Vector store initialized")
    print(f"Collection stats: {store.get_collection_stats()}")

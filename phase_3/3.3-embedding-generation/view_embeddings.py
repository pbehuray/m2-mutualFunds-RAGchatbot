"""
Script to view stored embeddings in the vector database.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '3.2-vector-database-setup', 'src'))

from vector_store import VectorStore


def main():
    """View stored embeddings."""
    persist_directory = str(Path(__file__).parent.parent / 'vector_db')
    
    print("=" * 60)
    print("Viewing Vector Database Contents")
    print("=" * 60)
    
    store = VectorStore(persist_directory=persist_directory)
    stats = store.get_collection_stats()
    
    print(f"\nCollection: {stats['collection_name']}")
    print(f"Total vectors: {stats['count']}")
    
    # Get all stored data including embeddings
    results = store.collection.get(include=['documents', 'metadatas', 'embeddings'])
    
    print(f"\nTotal documents: {len(results['ids'])}")
    
    for i, (doc_id, document, metadata, embedding) in enumerate(zip(
        results['ids'],
        results['documents'],
        results['metadatas'],
        results['embeddings']
    )):
        print(f"\n{'='*60}")
        print(f"Chunk {i+1}: {doc_id}")
        print(f"{'='*60}")
        print(f"Text (first 200 chars): {document[:200]}...")
        print(f"\nEmbedding (first 10 dims of {len(embedding)}): {embedding[:10]}")
        print(f"\nMetadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

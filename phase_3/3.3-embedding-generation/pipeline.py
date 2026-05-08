"""
Embedding Generation and Indexing Pipeline
Generates embeddings for chunks and indexes them in vector database.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '3.2-vector-database-setup', 'src'))

from embedding_generator import EmbeddingGenerator
from vector_store import VectorStore


class EmbeddingPipeline:
    """Pipeline for generating embeddings and indexing chunks."""
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the pipeline.
        
        Args:
            persist_directory: Directory to persist vector database
        """
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore(
            persist_directory=persist_directory,
            collection_name="mutual_fund_chunks"
        )
    
    def process_chunked_json(
        self,
        json_path: str
    ) -> Dict[str, Any]:
        """
        Process a single chunked JSON file.
        
        Args:
            json_path: Path to chunked JSON file
            
        Returns:
            Processing result
        """
        # Read JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get('chunks', [])
        scheme_name = data.get('scheme_name', '')
        
        if not chunks:
            return {
                'scheme_name': scheme_name,
                'file': json_path,
                'chunks_processed': 0,
                'error': 'No chunks found'
            }
        
        # Generate embeddings
        embeddings = self.embedding_generator.generate_embeddings_for_chunks(chunks)
        
        # Add to vector store
        self.vector_store.add_chunks(chunks, embeddings)
        
        return {
            'scheme_name': scheme_name,
            'file': json_path,
            'chunks_processed': len(chunks),
            'embedding_dim': len(embeddings[0]) if embeddings else 0
        }
    
    def process_directory(
        self,
        input_dir: str,
        persist_directory: str
    ) -> List[Dict[str, Any]]:
        """
        Process all chunked JSON files in a directory.
        
        Args:
            input_dir: Directory containing chunked JSON files
            persist_directory: Directory to persist vector database
            
        Returns:
            List of processing results
        """
        results = []
        
        # Process each JSON file
        for json_file in Path(input_dir).glob('*_chunked.json'):
            print(f"Processing: {json_file.name}")
            
            result = self.process_chunked_json(str(json_file))
            results.append(result)
            
            print(f"  Chunks processed: {result['chunks_processed']}")
            print(f"  Embedding dim: {result.get('embedding_dim', 'N/A')}")
        
        # Get final stats
        stats = self.vector_store.get_collection_stats()
        
        return results, stats


def main():
    """Main function to run the pipeline."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    chunked_json_dir = base_dir / 'phase_2' / 'scraped-data' / 'chunked_json'
    persist_directory = str(base_dir / 'phase_3' / 'vector_db')
    
    print("=" * 60)
    print("Embedding Generation and Indexing Pipeline")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = EmbeddingPipeline(persist_directory=persist_directory)
    
    # Print model info
    model_info = pipeline.embedding_generator.get_model_info()
    print(f"\nModel: {model_info['model_name']}")
    print(f"Embedding dimension: {model_info['embedding_dim']}")
    print(f"Max sequence length: {model_info['max_seq_length']}")
    
    # Process all chunked JSON files
    print(f"\nInput directory: {chunked_json_dir}")
    print(f"Vector DB directory: {persist_directory}\n")
    
    results, stats = pipeline.process_directory(
        str(chunked_json_dir),
        persist_directory
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("Processing Complete")
    print("=" * 60)
    
    total_chunks = sum(r['chunks_processed'] for r in results)
    print(f"Files processed: {len(results)}")
    print(f"Total chunks indexed: {total_chunks}")
    print(f"Total vectors in DB: {stats['count']}")
    print(f"\nVector database saved to: {persist_directory}")


if __name__ == "__main__":
    main()

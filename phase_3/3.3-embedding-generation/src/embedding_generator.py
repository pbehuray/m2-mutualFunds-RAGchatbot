"""
Embedding Generator Module
Generates embeddings using sentence-transformers (bge-small-en).
"""

from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
from pathlib import Path


class EmbeddingGenerator:
    """Embedding generator using sentence-transformers."""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=False)
        return embedding.tolist()
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def generate_embeddings_for_chunks(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[List[float]]:
        """
        Generate embeddings for chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of embedding vectors
        """
        texts = [chunk['text'] for chunk in chunks]
        return self.generate_embeddings(texts)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Dictionary with model info
        """
        return {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'max_seq_length': self.model.max_seq_length
        }


if __name__ == "__main__":
    # Test the embedding generator
    generator = EmbeddingGenerator()
    
    print(f"Model: {generator.model_name}")
    print(f"Embedding dimension: {generator.embedding_dim}")
    print(f"Max sequence length: {generator.model.max_seq_length}")
    
    # Test embedding
    test_text = "HDFC Flexi Cap Fund is a mutual fund scheme."
    embedding = generator.generate_embedding(test_text)
    print(f"Embedding length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

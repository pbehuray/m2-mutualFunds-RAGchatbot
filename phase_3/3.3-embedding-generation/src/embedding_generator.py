"""
Embedding Generator Module
Generates embeddings using an external embedding API or lightweight fallback.
"""

from typing import List, Dict, Any
import hashlib
import json
import math
import os
import requests
from pathlib import Path


class EmbeddingGenerator:
    """Embedding generator using an external API or lightweight fallback."""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name
        self.embedding_dim = int(os.environ.get("EMBEDDING_DIM", "384"))
        self.api_url = os.environ.get("EMBEDDING_API_URL")
        self.api_key = os.environ.get("EMBEDDING_API_KEY")
        self.api_model = os.environ.get("EMBEDDING_API_MODEL", model_name)
        self.api_provider = os.environ.get("EMBEDDING_API_PROVIDER", "openai").lower()
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self.api_url:
            return self._generate_embedding_with_api(text)
        return self._generate_embedding_with_hash(text)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.api_url:
            return [self._generate_embedding_with_api(text) for text in texts]
        return [self._generate_embedding_with_hash(text) for text in texts]

    def _generate_embedding_with_api(self, text: str) -> List[float]:
        if self.api_provider == "huggingface":
            payload = {"inputs": text}
        else:
            payload = {
                "model": self.api_model,
                "input": text,
            }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "data" in data:
            return data["data"][0]["embedding"]
        if isinstance(data, dict) and "embedding" in data:
            return data["embedding"]
        if isinstance(data, list) and data and isinstance(data[0], list):
            return data[0]
        if isinstance(data, list):
            return data
        raise ValueError("Embedding API response did not contain an embedding")

    def _generate_embedding_with_hash(self, text: str) -> List[float]:
        vector = [0.0] * self.embedding_dim
        tokens = text.lower().split()
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.embedding_dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
    
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
            'provider': 'api' if self.api_url else 'hash_fallback',
            'max_seq_length': None
        }


if __name__ == "__main__":
    # Test the embedding generator
    generator = EmbeddingGenerator()
    
    print(f"Model: {generator.model_name}")
    print(f"Embedding dimension: {generator.embedding_dim}")

    
    # Test embedding
    test_text = "HDFC Flexi Cap Fund is a mutual fund scheme."
    embedding = generator.generate_embedding(test_text)
    print(f"Embedding length: {len(embedding)}")

"""
Metadata Tagger Module
Adds metadata to chunks for tracking and retrieval.
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import asdict


class MetadataTagger:
    """Metadata tagger for adding rich metadata to chunks."""
    
    def __init__(self):
        """Initialize metadata tagger."""
        pass
    
    def tag_chunk(
        self,
        chunk_text: str,
        base_metadata: Dict[str, Any] = None,
        chunk_index: int = 0,
        total_chunks: int = 1
    ) -> Dict[str, Any]:
        """
        Add metadata to a chunk.
        
        Args:
            chunk_text: Chunk text content
            base_metadata: Base metadata to include
            chunk_index: Index of this chunk in the document
            total_chunks: Total number of chunks in the document
            
        Returns:
            Dictionary with metadata
        """
        if base_metadata is None:
            base_metadata = {}
        
        metadata = {
            **base_metadata,
            'chunk_index': chunk_index,
            'total_chunks': total_chunks,
            'chunk_length': len(chunk_text),
            'word_count': len(chunk_text.split()),
            'created_at': datetime.now().isoformat()
        }
        
        return metadata
    
    def add_source_metadata(
        self,
        metadata: Dict[str, Any],
        source_url: str,
        scheme_name: str,
        document_type: str = 'html'
    ) -> Dict[str, Any]:
        """
        Add source information to metadata.
        
        Args:
            metadata: Existing metadata
            source_url: Source URL
            scheme_name: Mutual fund scheme name
            document_type: Type of document (html, pdf, etc.)
            
        Returns:
            Updated metadata
        """
        metadata['source_url'] = source_url
        metadata['scheme_name'] = scheme_name
        metadata['document_type'] = document_type
        metadata['source_domain'] = self._extract_domain(source_url)
        
        return metadata
    
    def add_content_metadata(
        self,
        metadata: Dict[str, Any],
        chunk_text: str
    ) -> Dict[str, Any]:
        """
        Add content-related metadata.
        
        Args:
            metadata: Existing metadata
            chunk_text: Chunk text content
            
        Returns:
            Updated metadata
        """
        metadata['has_numbers'] = any(c.isdigit() for c in chunk_text)
        metadata['has_currency'] = any(c in chunk_text for c in ['₹', '$', '€', '£'])
        metadata['has_percentage'] = '%' in chunk_text
        metadata['sentence_count'] = self._count_sentences(chunk_text)
        metadata['avg_sentence_length'] = metadata['word_count'] / max(metadata['sentence_count'], 1)
        
        return metadata
    
    def add_section_metadata(
        self,
        metadata: Dict[str, Any],
        section_header: str = None,
        section_level: int = 0
    ) -> Dict[str, Any]:
        """
        Add section information to metadata.
        
        Args:
            metadata: Existing metadata
            section_header: Section header text
            section_level: Section hierarchy level (0-6)
            
        Returns:
            Updated metadata
        """
        if section_header:
            metadata['section_header'] = section_header
            metadata['section_level'] = section_level
        
        return metadata
    
    def create_chunk_id(
        self,
        scheme_name: str,
        chunk_index: int,
        chunk_type: str = 'section'
    ) -> str:
        """
        Create a unique chunk ID.
        
        Args:
            scheme_name: Scheme name
            chunk_index: Chunk index
            chunk_type: Type of chunk
            
        Returns:
            Unique chunk ID
        """
        # Clean scheme name
        clean_name = scheme_name.lower().replace(' ', '_').replace('-', '_')
        
        chunk_id = f"{clean_name}_{chunk_type}_{chunk_index}"
        
        return chunk_id
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name
        """
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def _count_sentences(self, text: str) -> int:
        """
        Count sentences in text.
        
        Args:
            text: Text to count sentences in
            
        Returns:
            Number of sentences
        """
        import re
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def serialize_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Serialize metadata to JSON string.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            JSON string
        """
        return json.dumps(metadata, indent=2, ensure_ascii=False)
    
    def deserialize_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """
        Deserialize metadata from JSON string.
        
        Args:
            metadata_str: JSON string
            
        Returns:
            Metadata dictionary
        """
        return json.loads(metadata_str)


if __name__ == "__main__":
    # Test the metadata tagger
    tagger = MetadataTagger()
    
    chunk_text = "This is a test chunk with ₹100 and 50% returns."
    
    # Create base metadata
    metadata = tagger.tag_chunk(
        chunk_text,
        chunk_index=0,
        total_chunks=5
    )
    
    # Add source metadata
    metadata = tagger.add_source_metadata(
        metadata,
        source_url="https://groww.in/mutual-funds/hdfc-large-cap-fund",
        scheme_name="HDFC Large Cap Fund"
    )
    
    # Add content metadata
    metadata = tagger.add_content_metadata(metadata, chunk_text)
    
    # Add section metadata
    metadata = tagger.add_section_metadata(
        metadata,
        section_header="Overview",
        section_level=1
    )
    
    print("Metadata:")
    print(tagger.serialize_metadata(metadata))

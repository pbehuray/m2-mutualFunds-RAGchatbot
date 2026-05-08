"""
Semantic Chunker Module
Implements semantic chunking algorithm based on sections and headers.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    text: str
    chunk_id: int
    metadata: Dict[str, Any]
    start_position: int
    end_position: int


class SemanticChunker:
    """Semantic chunker for splitting documents into meaningful chunks."""
    
    def __init__(
        self,
        chunk_size: int = 800,
        overlap: int = 100,
        min_chunk_size: int = 100
    ):
        """
        Initialize semantic chunker.
        
        Args:
            chunk_size: Target chunk size in tokens (approximate)
            overlap: Overlap between chunks in tokens
            min_chunk_size: Minimum chunk size in tokens
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_by_sections(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """
        Chunk text by sections based on headers.
        
        Args:
            text: Text to chunk
            metadata: Base metadata for all chunks
            
        Returns:
            List of chunks
        """
        if metadata is None:
            metadata = {}
        
        # Split by headers (# ## ### etc.)
        sections = self._split_by_headers(text)
        
        chunks = []
        chunk_id = 0
        current_position = 0
        
        for section in sections:
            section_text = section['text']
            section_header = section['header']
            
            # If section is small enough, keep it as one chunk
            if len(section_text) <= self.chunk_size:
                chunk_metadata = {
                    **metadata,
                    'section_header': section_header,
                    'chunk_type': 'section'
                }
                
                chunk = Chunk(
                    text=section_text,
                    chunk_id=chunk_id,
                    metadata=chunk_metadata,
                    start_position=current_position,
                    end_position=current_position + len(section_text)
                )
                chunks.append(chunk)
                chunk_id += 1
                current_position += len(section_text)
            else:
                # Split large sections into smaller chunks
                sub_chunks = self._chunk_large_text(
                    section_text,
                    chunk_id,
                    current_position,
                    {**metadata, 'section_header': section_header, 'chunk_type': 'subsection'}
                )
                chunks.extend(sub_chunks)
                chunk_id += len(sub_chunks)
                current_position += len(section_text)
        
        return chunks
    
    def _split_by_headers(self, text: str) -> List[Dict[str, str]]:
        """
        Split text by markdown-style headers.
        
        Args:
            text: Text to split
            
        Returns:
            List of sections with headers
        """
        sections = []
        lines = text.split('\n')
        
        current_section = []
        current_header = "Introduction"
        
        for line in lines:
            # Check if line is a header
            if line.strip().startswith('#'):
                # Save previous section
                if current_section:
                    sections.append({
                        'header': current_header,
                        'text': '\n'.join(current_section).strip()
                    })
                
                # Start new section
                current_header = line.strip().lstrip('#').strip()
                current_section = []
            else:
                current_section.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                'header': current_header,
                'text': '\n'.join(current_section).strip()
            })
        
        return sections
    
    def _chunk_large_text(
        self,
        text: str,
        start_chunk_id: int,
        start_position: int,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """
        Chunk large text into smaller pieces with overlap.
        
        Args:
            text: Text to chunk
            start_chunk_id: Starting chunk ID
            start_position: Starting position in original text
            metadata: Metadata for chunks
            
        Returns:
            List of chunks
        """
        chunks = []
        sentences = self._split_into_sentences(text)
        
        current_chunk = []
        current_length = 0
        chunk_id = start_chunk_id
        current_pos = start_position
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # Check if adding this sentence would exceed chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                
                chunk = Chunk(
                    text=chunk_text,
                    chunk_id=chunk_id,
                    metadata={**metadata, 'subchunk_id': len(chunks)},
                    start_position=current_pos,
                    end_position=current_pos + len(chunk_text)
                )
                chunks.append(chunk)
                chunk_id += 1
                current_pos += len(chunk_text)
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences
                current_length = sum(len(s) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunk_text = ' '.join(current_chunk)
            
            chunk = Chunk(
                text=chunk_text,
                chunk_id=chunk_id,
                metadata={**metadata, 'subchunk_id': len(chunks)},
                start_position=current_pos,
                end_position=current_pos + len(chunk_text)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """
        Get sentences for overlap.
        
        Args:
            sentences: Current chunk sentences
            
        Returns:
            Sentences to include in overlap
        """
        # Calculate overlap in terms of sentences
        overlap_length = sum(len(s) for s in sentences)
        target_overlap = min(self.overlap, overlap_length // 2)
        
        overlap_sentences = []
        current_length = 0
        
        # Take sentences from the end for overlap
        for sentence in reversed(sentences):
            if current_length + len(sentence) <= target_overlap:
                overlap_sentences.insert(0, sentence)
                current_length += len(sentence)
            else:
                break
        
        return overlap_sentences
    
    def chunk_by_paragraphs(self, text: str, metadata: Dict[str, Any] = None) -> List[Chunk]:
        """
        Chunk text by paragraphs.
        
        Args:
            text: Text to chunk
            metadata: Base metadata for all chunks
            
        Returns:
            List of chunks
        """
        if metadata is None:
            metadata = {}
        
        paragraphs = text.split('\n\n')
        chunks = []
        chunk_id = 0
        current_position = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            chunk_metadata = {
                **metadata,
                'chunk_type': 'paragraph'
            }
            
            chunk = Chunk(
                text=paragraph,
                chunk_id=chunk_id,
                metadata=chunk_metadata,
                start_position=current_position,
                end_position=current_position + len(paragraph)
            )
            chunks.append(chunk)
            chunk_id += 1
            current_position += len(paragraph) + 2  # +2 for \n\n
        
        return chunks


if __name__ == "__main__":
    # Test the semantic chunker
    chunker = SemanticChunker(chunk_size=800, overlap=100)
    
    test_text = """
    # Introduction
    This is the introduction paragraph. It provides an overview of the document.
    
    # Section 1
    This is section 1. It contains important information about the topic.
    This section has multiple paragraphs to test the chunking algorithm.
    Here is another paragraph in section 1 with more content.
    
    # Section 2
    This is section 2. It also contains relevant information.
    The semantic chunker should split this into separate chunks based on headers.
    """
    
    print("Chunking by sections:")
    chunks = chunker.chunk_by_sections(test_text, metadata={'source': 'test'})
    
    for chunk in chunks:
        print(f"\nChunk {chunk.chunk_id}:")
        print(f"Text: {chunk.text[:100]}...")
        print(f"Metadata: {chunk.metadata}")
        print(f"Length: {len(chunk.text)}")

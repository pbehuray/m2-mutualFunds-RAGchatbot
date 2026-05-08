"""
Chunk Validator Module
Validates chunk quality and coherence.
"""

import re
from typing import Dict, Any, List, Tuple


class ChunkValidator:
    """Validator for checking chunk quality and coherence."""
    
    def __init__(
        self,
        min_length: int = 50,
        max_length: int = 2000,
        min_words: int = 10,
        max_words: int = 500
    ):
        """
        Initialize chunk validator.
        
        Args:
            min_length: Minimum character length
            max_length: Maximum character length
            min_words: Minimum word count
            max_words: Maximum word count
        """
        self.min_length = min_length
        self.max_length = max_length
        self.min_words = min_words
        self.max_words = max_words
    
    def validate_chunk(self, chunk_text: str) -> Tuple[bool, List[str]]:
        """
        Validate a chunk.
        
        Args:
            chunk_text: Chunk text to validate
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check length
        if len(chunk_text) < self.min_length:
            issues.append(f"Chunk too short: {len(chunk_text)} characters (minimum: {self.min_length})")
        
        if len(chunk_text) > self.max_length:
            issues.append(f"Chunk too long: {len(chunk_text)} characters (maximum: {self.max_length})")
        
        # Check word count
        word_count = len(chunk_text.split())
        if word_count < self.min_words:
            issues.append(f"Too few words: {word_count} (minimum: {self.min_words})")
        
        if word_count > self.max_words:
            issues.append(f"Too many words: {word_count} (maximum: {self.max_words})")
        
        # Check for empty or whitespace-only
        if not chunk_text.strip():
            issues.append("Chunk is empty or whitespace only")
        
        # Check for coherence
        coherence_issues = self._check_coherence(chunk_text)
        issues.extend(coherence_issues)
        
        is_valid = len(issues) == 0
        
        return is_valid, issues
    
    def _check_coherence(self, text: str) -> List[str]:
        """
        Check text coherence.
        
        Args:
            text: Text to check
            
        Returns:
            List of coherence issues
        """
        issues = []
        
        # Check for sentence fragments (sentences ending without proper punctuation)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            # Check if sentence is too short
            if len(sentence.split()) < 3:
                issues.append(f"Possible sentence fragment: '{sentence[:50]}...'")
        
        # Check for excessive repetition
        if self._has_excessive_repetition(text):
            issues.append("Chunk has excessive repetition")
        
        # Check for broken words at boundaries
        if self._has_broken_words(text):
            issues.append("Chunk may have broken words at boundaries")
        
        return issues
    
    def _has_excessive_repetition(self, text: str, threshold: int = 3) -> bool:
        """
        Check for excessive repetition of words or phrases.
        
        Args:
            text: Text to check
            threshold: Maximum allowed repetitions
            
        Returns:
            True if excessive repetition found
        """
        words = text.lower().split()
        word_counts = {}
        
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Check if any word repeats excessively
        for word, count in word_counts.items():
            if count > threshold and len(word) > 3:  # Ignore short common words
                return True
        
        return False
    
    def _has_broken_words(self, text: str) -> bool:
        """
        Check for broken words at chunk boundaries.
        
        Args:
            text: Text to check
            
        Returns:
            True if broken words detected
        """
        # Check if text ends with a hyphen (possible broken word)
        if text.rstrip().endswith('-'):
            return True
        
        # Check if text starts with lowercase letter (possible continuation)
        if text and text[0].islower() and not text.startswith('['):
            return True
        
        return False
    
    def validate_chunk_sequence(self, chunks: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate a sequence of chunks for consistency.
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Validate each chunk individually
        for i, chunk in enumerate(chunks):
            is_valid, chunk_issues = self.validate_chunk(chunk)
            if not is_valid:
                issues.append(f"Chunk {i}: {', '.join(chunk_issues)}")
        
        # Check overlap between chunks
        overlap_issues = self._check_overlaps(chunks)
        issues.extend(overlap_issues)
        
        # Check for content gaps
        gap_issues = self._check_content_gaps(chunks)
        issues.extend(gap_issues)
        
        is_valid = len(issues) == 0
        
        return is_valid, issues
    
    def _check_overlaps(self, chunks: List[str]) -> List[str]:
        """
        Check overlaps between consecutive chunks.
        
        Args:
            chunks: List of chunks
            
        Returns:
            List of overlap issues
        """
        issues = []
        
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Get last sentence of current chunk
            current_sentences = re.split(r'[.!?]+', current_chunk)
            current_last = current_sentences[-1].strip() if current_sentences else ""
            
            # Get first sentence of next chunk
            next_sentences = re.split(r'[.!?]+', next_chunk)
            next_first = next_sentences[0].strip() if next_sentences else ""
            
            # Check for exact match (too much overlap)
            if current_last == next_first:
                issues.append(f"Chunks {i} and {i+1} have exact overlap: '{current_last}'")
        
        return issues
    
    def _check_content_gaps(self, chunks: List[str]) -> List[str]:
        """
        Check for content gaps between chunks.
        
        Args:
            chunks: List of chunks
            
        Returns:
            List of gap issues
        """
        issues = []
        
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Check if chunks end/start abruptly
            if not current_chunk.rstrip().endswith(('.', '!', '?')):
                issues.append(f"Chunk {i} does not end with sentence-ending punctuation")
            
            if next_chunk and next_chunk[0].islower() and not next_chunk.startswith('['):
                issues.append(f"Chunk {i+1} starts with lowercase (possible continuation)")
        
        return issues
    
    def get_quality_score(self, chunk_text: str) -> float:
        """
        Get quality score for a chunk (0.0 to 1.0).
        
        Args:
            chunk_text: Chunk text to score
            
        Returns:
            Quality score
        """
        score = 1.0
        
        # Deduct for length issues
        length = len(chunk_text)
        if length < self.min_length:
            score -= 0.3 * (1 - length / self.min_length)
        elif length > self.max_length:
            score -= 0.2 * (length / self.max_length - 1)
        
        # Deduct for word count issues
        word_count = len(chunk_text.split())
        if word_count < self.min_words:
            score -= 0.2 * (1 - word_count / self.min_words)
        elif word_count > self.max_words:
            score -= 0.1 * (word_count / self.max_words - 1)
        
        # Deduct for coherence issues
        if self._has_excessive_repetition(chunk_text):
            score -= 0.2
        
        if self._has_broken_words(chunk_text):
            score -= 0.1
        
        return max(0.0, min(1.0, score))


if __name__ == "__main__":
    # Test the chunk validator
    validator = ChunkValidator()
    
    # Test valid chunk
    valid_chunk = "This is a valid chunk. It has proper sentences and reasonable length. It should pass validation."
    is_valid, issues = validator.validate_chunk(valid_chunk)
    print(f"Valid chunk: {is_valid}, Issues: {issues}")
    print(f"Quality score: {validator.get_quality_score(valid_chunk)}")
    
    # Test invalid chunk (too short)
    short_chunk = "Too short."
    is_valid, issues = validator.validate_chunk(short_chunk)
    print(f"\nShort chunk: {is_valid}, Issues: {issues}")
    print(f"Quality score: {validator.get_quality_score(short_chunk)}")
    
    # Test chunk sequence
    chunks = [
        "First chunk with proper ending.",
        "Second chunk with proper start. It continues well."
    ]
    is_valid, issues = validator.validate_chunk_sequence(chunks)
    print(f"\nChunk sequence: {is_valid}, Issues: {issues}")

"""
Chunking strategy implementations.
"""
from typing import List
from .interfaces import Chunker


class FixedSizeChunker(Chunker):
    """
    Chunks text into fixed-size pieces with optional overlap.
    
    Larger documents produce more chunks automatically.
    """
    
    def __init__(self, chunk_size: int, overlap: int = 0):
        """
        Initialize chunker with fixed chunk size.
        
        :param chunk_size: Number of characters per chunk (must be > 0)
        :param overlap: Number of overlapping characters between chunks (must be >= 0 and < chunk_size)
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str) -> List[str]:
        """
        Split text into fixed-size chunks.
        
        :param text: The text to chunk
        :returns: List of text chunks (all non-empty strings)
        """
        if not text:
            return []
        
        chunks = []
        step = self.chunk_size - self.overlap
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start += step
        
        return chunks if chunks else [text]
    
    def get_chunk_count_estimate(self, text_length: int) -> int:
        """
        Estimate chunks for given text length.
        
        :param text_length: Length of text in characters (must be >= 0)
        :returns: Estimated number of chunks (always >= 1)
        """
        if text_length == 0:
            return 1
        
        step = self.chunk_size - self.overlap
        return max(1, (text_length + step - 1) // step)


class SentenceAwareChunker(Chunker):
    """
    Chunks text by sentences, maintaining semantic boundaries.
    
    Tries to create chunks near target size while respecting sentence boundaries.
    Larger documents produce more chunks.
    """
    
    def __init__(self, target_chunk_size: int, max_chunk_size: int = None):
        """
        Initialize sentence-aware chunker.
        
        :param target_chunk_size: Target number of characters per chunk (must be > 0)
        :param max_chunk_size: Maximum allowed chunk size (defaults to 2x target, must be >= target_chunk_size if provided)
        """
        if target_chunk_size <= 0:
            raise ValueError("target_chunk_size must be positive")
        if max_chunk_size is not None and max_chunk_size < target_chunk_size:
            raise ValueError("max_chunk_size must be >= target_chunk_size")
        
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size or (target_chunk_size * 2)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        :param text: Text to split
        :returns: List of sentences
        """
        import re
        sentence_endings = re.compile(r'[.!?]+[\s\n]+|[.!?]+$')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk(self, text: str) -> List[str]:
        """
        Split text into sentence-aware chunks.
        
        :param text: The text to chunk
        :returns: List of text chunks (all non-empty strings)
        """
        if not text:
            return []
        
        sentences = self._split_into_sentences(text)
        if not sentences:
            return [text]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            elif current_size + sentence_size > self.target_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text]
    
    def get_chunk_count_estimate(self, text_length: int) -> int:
        """
        Estimate chunks for given text length.
        
        :param text_length: Length of text in characters (must be >= 0)
        :returns: Estimated number of chunks (always >= 1)
        """
        if text_length == 0:
            return 1
        
        return max(1, (text_length + self.target_chunk_size - 1) // self.target_chunk_size)

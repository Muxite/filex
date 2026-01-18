"""
Interfaces for embedding and chunking components.
"""
from abc import ABC, abstractmethod
from typing import Protocol, List
import numpy as np


class Embedder(Protocol):
    """
    Protocol defining the interface for text embedding models.
    
    Implementations should provide a method to convert text into
    numerical vector representations suitable for semantic search.
    """
    
    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for a single text string.
        
        :param text: The text to embed
        :returns: A numpy array representing the embedding vector
        :raises ValueError: If text is empty or invalid
        """
        ...
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embedding vectors for multiple texts efficiently.
        
        :param texts: List of texts to embed
        :returns: A 2D numpy array where each row is an embedding vector
        :raises ValueError: If texts list is empty
        """
        ...


class Chunker(ABC):
    """
    Abstract base class for text chunking strategies.
    
    Chunkers split documents into smaller pieces for embedding.
    Larger documents should produce more chunks.
    """
    
    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        """
        Split text into chunks according to the chunking strategy.
        
        :param text: The text to chunk
        :returns: List of text chunks
        :postcondition: All returned chunks are non-empty strings
        """
        pass
    
    @abstractmethod
    def get_chunk_count_estimate(self, text_length: int) -> int:
        """
        Estimate the number of chunks that would be produced for text of given length.
        
        :param text_length: Length of text in characters (must be >= 0)
        :returns: Estimated number of chunks (always >= 1)
        """
        pass

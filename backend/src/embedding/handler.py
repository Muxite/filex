"""
Text embedding handler with dependency injection and configurable chunking.
"""
from typing import List, Optional, Tuple
import numpy as np
from pathlib import Path

from .interfaces import Embedder, Chunker
from .file_extractors import FileExtractor
from ..logger import get_logger


class TextEmbeddingHandler:
    """
    Handles text embedding generation for documents with configurable chunking.
    
    Uses dependency injection for embedder and chunker. Larger documents
    automatically produce more chunks and thus more embedding vectors.
    """
    
    def __init__(
        self,
        embedder: Embedder,
        chunker: Optional[Chunker] = None
    ):
        """
        Initialize the embedding handler with dependency injection.
        
        :param embedder: The embedder to use (injected dependency, must not be None)
        :param chunker: The chunking strategy to use (optional, defaults to FixedSizeChunker)
        """
        self.logger = get_logger(__name__)
        
        if embedder is None:
            self.logger.error("embedder cannot be None")
            raise ValueError("embedder cannot be None")
        
        self.embedder = embedder
        
        if chunker is None:
            from .chunkers import FixedSizeChunker
            chunker = FixedSizeChunker(chunk_size=512, overlap=50)
            self.logger.debug("Using default FixedSizeChunker (chunk_size=512, overlap=50)")
        
        self.chunker = chunker
        self.logger.info("TextEmbeddingHandler initialized")
    
    def set_chunker(self, chunker: Chunker) -> None:
        """
        Set or change the chunking strategy.
        
        :param chunker: The new chunking strategy (must not be None)
        """
        if chunker is None:
            self.logger.error("chunker cannot be None")
            raise ValueError("chunker cannot be None")
        
        self.chunker = chunker
        self.logger.info(f"Chunker changed to {type(chunker).__name__}")
    
    def embed_file(self, file_path: str) -> Tuple[List[str], np.ndarray]:
        """
        Extract text from a file, chunk it, and generate embeddings.
        
        :param file_path: Path to the file to embed (must exist and be readable)
        :returns: Tuple of (chunks, embeddings) where embeddings is a 2D array
        :postcondition: embeddings.shape[0] == len(chunks)
        """
        self.logger.info(f"Starting embedding generation for file: {file_path}")
        text = FileExtractor.extract_text(file_path)
        self.logger.debug(f"Extracted {len(text)} characters from file")
        
        result = self.embed_text(text)
        self.logger.info(f"Generated {len(result[0])} chunks and embeddings for file: {file_path}")
        return result
    
    def embed_text(self, text: str) -> Tuple[List[str], np.ndarray]:
        """
        Chunk text and generate embeddings for each chunk.
        
        :param text: The text to embed (must not be empty)
        :returns: Tuple of (chunks, embeddings) where embeddings is a 2D array
        :postcondition: embeddings.shape[0] == len(chunks)
        """
        if not text:
            self.logger.error("Cannot embed empty text")
            raise ValueError("text cannot be empty")
        
        self.logger.debug(f"Chunking text of length {len(text)} characters")
        chunks = self.chunker.chunk(text)
        self.logger.debug(f"Text chunked into {len(chunks)} chunks")
        
        if not chunks:
            self.logger.error("Chunker produced no chunks")
            raise ValueError("chunker produced no chunks")
        
        try:
            self.logger.debug("Generating embeddings using embed_batch")
            embeddings = self.embedder.embed_batch(chunks)
        except AttributeError:
            self.logger.debug("embed_batch not available, using individual embed calls")
            embeddings = np.array([self.embedder.embed(chunk) for chunk in chunks])
        
        if embeddings.shape[0] != len(chunks):
            self.logger.error(
                f"Embedding count mismatch: expected {len(chunks)}, got {embeddings.shape[0]}"
            )
            raise RuntimeError(
                f"Embedding count mismatch: expected {len(chunks)}, got {embeddings.shape[0]}"
            )
        
        self.logger.debug(
            f"Generated embeddings: shape {embeddings.shape}, dimension {embeddings.shape[1]}"
        )
        return chunks, embeddings
    
    def get_estimated_chunk_count(self, text: str) -> int:
        """
        Estimate the number of chunks that would be produced for given text.
        
        :param text: The text to estimate
        :returns: Estimated number of chunks (always >= 1)
        """
        if not text:
            return 1
        
        return self.chunker.get_chunk_count_estimate(len(text))
    
    def get_file_estimated_chunk_count(self, file_path: str) -> int:
        """
        Estimate the number of chunks for a file without reading full content.
        
        Uses file size as a proxy for text length.
        
        :param file_path: Path to the file (must exist)
        :returns: Estimated number of chunks (always >= 1)
        """
        file_size = FileExtractor.get_file_size(file_path)
        estimate = max(1, self.chunker.get_chunk_count_estimate(file_size))
        self.logger.debug(
            f"Estimated {estimate} chunks for file {file_path} (size: {file_size} bytes)"
        )
        return estimate

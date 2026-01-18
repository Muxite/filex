"""
File handlers for processing different file types.
"""
from typing import Protocol, Optional, Dict, Any
from abc import ABC, abstractmethod
import numpy as np

from .file_metadata import FileMetadata
from .embedding.handler import TextEmbeddingHandler
from .logger import get_logger


class FileHandler(Protocol):
    """
    Protocol defining the interface for file handlers.
    
    Handlers process files and return results specific to their file type.
    """
    
    def can_handle(self, metadata: FileMetadata) -> bool:
        """
        Check if this handler can process the given file.
        
        :param metadata: File metadata
        :returns: True if this handler can process the file
        """
        ...
    
    def process(self, metadata: FileMetadata) -> Dict[str, Any]:
        """
        Process the file and return results.
        
        :param metadata: File metadata
        :returns: Dictionary with processing results
        """
        ...


class TextFileHandler:
    """
    Handler for text-based files (.txt, .docx) that generates embeddings.
    
    Uses dependency injection for the TextEmbeddingHandler.
    """
    
    def __init__(self, embedding_handler: TextEmbeddingHandler):
        """
        Initialize text file handler with embedding handler.
        
        :param embedding_handler: The TextEmbeddingHandler to use for embeddings (must not be None)
        """
        self.logger = get_logger(__name__)
        
        if embedding_handler is None:
            self.logger.error("embedding_handler cannot be None")
            raise ValueError("embedding_handler cannot be None")
        
        self.embedding_handler = embedding_handler
        self.supported_extensions = {'.txt', '.docx'}
        self.logger.info("TextFileHandler initialized")
    
    def can_handle(self, metadata: FileMetadata) -> bool:
        """
        Check if this handler can process the file.
        
        :param metadata: File metadata
        :returns: True if file is a supported text type
        """
        can_handle = metadata.is_text_type and metadata.file_extension in self.supported_extensions
        if can_handle:
            self.logger.debug(f"TextFileHandler can handle file: {metadata.file_name}")
        return can_handle
    
    def process(self, metadata: FileMetadata) -> Dict[str, Any]:
        """
        Process text file and generate embeddings.
        
        :param metadata: File metadata (must be a text file)
        :returns: Dictionary containing metadata and embedding results
        """
        if not self.can_handle(metadata):
            self.logger.error(f"Cannot handle file type: {metadata.file_extension}")
            raise ValueError(f"Cannot handle file type: {metadata.file_extension}")
        
        self.logger.info(
            f"Processing text file: {metadata.file_name} "
            f"({metadata.file_size_kb:.2f} KB)"
        )
        
        chunks, embeddings = self.embedding_handler.embed_file(metadata.file_path)
        
        embedding_dim = embeddings.shape[1] if len(embeddings.shape) > 1 else embeddings.shape[0]
        self.logger.info(
            f"Successfully processed text file: {metadata.file_name} "
            f"({len(chunks)} chunks, embedding dimension: {embedding_dim})"
        )
        
        return {
            "metadata": {
                "file_path": metadata.file_path,
                "file_name": metadata.file_name,
                "file_extension": metadata.file_extension,
                "file_size_bytes": metadata.file_size_bytes,
                "file_size_kb": metadata.file_size_kb,
                "file_size_mb": metadata.file_size_mb,
                "modified_time": metadata.modified_time.isoformat() if metadata.modified_time else None,
                "created_time": metadata.created_time.isoformat() if metadata.created_time else None,
            },
            "embeddings": {
                "chunks": chunks,
                "embeddings": embeddings,
                "num_chunks": len(chunks),
                "embedding_dimension": embedding_dim,
            },
            "processed": True,
        }


class DefaultFileHandler:
    """
    Default handler for unsupported file types.
    
    Returns file metadata only without processing.
    """
    
    def __init__(self):
        """Initialize default file handler."""
        self.logger = get_logger(__name__)
        self.logger.debug("DefaultFileHandler initialized")
    
    def can_handle(self, metadata: FileMetadata) -> bool:
        """
        Default handler can handle any file (returns True always).
        
        :param metadata: File metadata
        :returns: Always True
        """
        return True
    
    def process(self, metadata: FileMetadata) -> Dict[str, Any]:
        """
        Process file by returning metadata only.
        
        :param metadata: File metadata
        :returns: Dictionary containing only file metadata
        """
        self.logger.info(
            f"Using default handler for unsupported file type: {metadata.file_name} "
            f"({metadata.file_extension}, {metadata.file_size_kb:.2f} KB)"
        )
        
        reason = f"File type '{metadata.file_extension}' is not supported for embedding processing"
        self.logger.debug(f"Reason: {reason}")
        
        return {
            "metadata": {
                "file_path": metadata.file_path,
                "file_name": metadata.file_name,
                "file_extension": metadata.file_extension,
                "file_size_bytes": metadata.file_size_bytes,
                "file_size_kb": metadata.file_size_kb,
                "file_size_mb": metadata.file_size_mb,
                "modified_time": metadata.modified_time.isoformat() if metadata.modified_time else None,
                "created_time": metadata.created_time.isoformat() if metadata.created_time else None,
            },
            "embeddings": None,
            "processed": False,
            "reason": reason,
        }

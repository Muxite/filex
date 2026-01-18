"""
FileX backend package for semantic file indexing and search.
"""
from .embedding import (
    TextEmbeddingHandler,
    Embedder,
    Chunker,
    FixedSizeChunker,
    SentenceAwareChunker,
    SentenceTransformerEmbedder,
    FileExtractor,
)
from .file_metadata import FileMetadata
from .file_handlers import FileHandler, TextFileHandler, DefaultFileHandler
from .file_processor import FileProcessorRouter
from .logger import get_logger, configure_logging
from .repository import Repository, RepositoryConfig
from .index_manager import IndexManager, FileIndexEntry
from .storage_manager import StorageManager
from .repo_manager import RepositoryManager

__all__ = [
    "TextEmbeddingHandler",
    "Embedder",
    "Chunker",
    "FixedSizeChunker",
    "SentenceAwareChunker",
    "SentenceTransformerEmbedder",
    "FileExtractor",
    "FileMetadata",
    "FileHandler",
    "TextFileHandler",
    "DefaultFileHandler",
    "FileProcessorRouter",
    "get_logger",
    "configure_logging",
    "Repository",
    "RepositoryConfig",
    "IndexManager",
    "FileIndexEntry",
    "StorageManager",
    "RepositoryManager",
]

"""
Text embedding module with dependency injection and configurable chunking.
"""
from .handler import TextEmbeddingHandler
from .interfaces import Embedder, Chunker
from .chunkers import FixedSizeChunker, SentenceAwareChunker
from .embedders import SentenceTransformerEmbedder
from .file_extractors import FileExtractor
from .file_metadata import FileMetadata
from .file_handlers import FileHandler, TextFileHandler, DefaultFileHandler
from .file_processor import FileProcessorRouter
from .logger import get_logger, configure_logging
from .repository import Repository, RepositoryConfig
from .index_manager import IndexManager, FileIndexEntry
from .storage_manager import StorageManager
from .repo_manager import RepositoryManager
from .search_manager import SearchManager, SearchResult

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
    "SearchManager",
    "SearchResult",
]

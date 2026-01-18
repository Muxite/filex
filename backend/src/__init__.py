"""
Core FileX components for repository management and file processing.
"""
from .logger import get_logger, configure_logging
from .repository import Repository, RepositoryConfig
from .file_metadata import FileMetadata
from .file_processor import FileProcessorRouter
from .index_manager import IndexManager, FileIndexEntry
from .storage_manager import StorageManager
from .search_manager import SearchManager, SearchResult
from .repo_manager import RepositoryManager
from .file_handlers import TextFileHandler, DefaultFileHandler
from .image_handlers import ImageFileHandler
from .handler import TextEmbeddingHandler
from .embedders import SentenceTransformerEmbedder
from .image_embedders import CLIPImageEmbedder
from .chunkers import FixedSizeChunker, SentenceAwareChunker

__all__ = [
    "get_logger",
    "configure_logging",
    "Repository",
    "RepositoryConfig",
    "FileMetadata",
    "FileProcessorRouter",
    "IndexManager",
    "FileIndexEntry",
    "StorageManager",
    "SearchManager",
    "SearchResult",
    "RepositoryManager",
    "TextFileHandler",
    "ImageFileHandler",
    "DefaultFileHandler",
    "TextEmbeddingHandler",
    "SentenceTransformerEmbedder",
    "CLIPImageEmbedder",
    "FixedSizeChunker",
    "SentenceAwareChunker",
]

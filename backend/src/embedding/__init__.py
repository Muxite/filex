"""
Core embedding module with dependency injection and configurable chunking.
"""
from .handler import TextEmbeddingHandler
from .interfaces import Embedder, Chunker
from .chunkers import FixedSizeChunker, SentenceAwareChunker
from .embedders import SentenceTransformerEmbedder
from .file_extractors import FileExtractor

__all__ = [
    "TextEmbeddingHandler",
    "Embedder",
    "Chunker",
    "FixedSizeChunker",
    "SentenceAwareChunker",
    "SentenceTransformerEmbedder",
    "FileExtractor",
]

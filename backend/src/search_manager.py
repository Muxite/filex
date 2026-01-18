"""
Search manager for semantic search over indexed embeddings.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pickle
import json

from .repository import Repository
from .logger import get_logger


class SearchResult:
    """
    Represents a single search result with file and chunk information.
    """
    def __init__(
        self,
        file_path: str,
        chunk_index: int,
        chunk_text: str,
        similarity_score: float,
        file_name: Optional[str] = None,
    ):
        self.file_path = file_path
        self.chunk_index = chunk_index
        self.chunk_text = chunk_text
        self.similarity_score = similarity_score
        self.file_name = file_name or Path(file_path).name
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert search result to dictionary.
        
        :returns: Dictionary representation
        """
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "chunk_index": self.chunk_index,
            "chunk_text": self.chunk_text,
            "similarity_score": float(self.similarity_score),
        }


class SearchManager:
    """
    Manages searchable embeddings data for semantic search.
    
    Maintains a separate search index that can be updated incrementally
    as files are indexed. Supports cosine similarity search.
    """
    
    SEARCH_INDEX_NAME = "search_index.npy"
    SEARCH_METADATA_NAME = "search_metadata.json"
    
    def __init__(self, repository: Repository):
        """
        Initialize search manager with repository.
        
        :param repository: Repository instance (must not be None)
        """
        self.logger = get_logger(__name__)
        
        if repository is None:
            self.logger.error("repository cannot be None")
            raise ValueError("repository cannot be None")
        
        self.repository = repository
        self.index_dir = repository.config.index_dir
        self.search_index_path = self.index_dir / self.SEARCH_INDEX_NAME
        self.search_metadata_path = self.index_dir / self.SEARCH_METADATA_NAME
        
        self._embeddings: Optional[np.ndarray] = None
        self._metadata: List[Dict[str, Any]] = []
        self._load_search_data()
        
        self.logger.info("SearchManager initialized")
    
    def _load_search_data(self) -> None:
        """
        Load search index and metadata from disk.
        """
        if self.search_index_path.exists() and self.search_metadata_path.exists():
            try:
                self._embeddings = np.load(self.search_index_path)
                with open(self.search_metadata_path, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
                self.logger.info(
                    f"Loaded search index: {len(self._metadata)} chunks, "
                    f"embeddings shape: {self._embeddings.shape}"
                )
            except Exception as e:
                self.logger.warning(f"Failed to load search data: {e}, starting fresh")
                self._embeddings = None
                self._metadata = []
        else:
            self._embeddings = None
            self._metadata = []
            self.logger.debug("No existing search index found, starting fresh")
    
    def _save_search_data(self) -> None:
        """
        Save search index and metadata to disk.
        """
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        if self._embeddings is not None and len(self._embeddings) > 0:
            np.save(self.search_index_path, self._embeddings)
            with open(self.search_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, indent=2, ensure_ascii=False)
            self.logger.debug(
                f"Saved search index: {len(self._metadata)} chunks, "
                f"embeddings shape: {self._embeddings.shape}"
            )
        else:
            self.logger.debug("No search data to save")
    
    def add_file_embeddings(
        self,
        file_path: str,
        chunks: List[str],
        embeddings: np.ndarray,
    ) -> None:
        """
        Add or update embeddings for a file in the search index.
        
        Removes old embeddings for the file if they exist, then adds new ones.
        Updates search data immediately.
        
        :param file_path: Path to the file
        :param chunks: List of text chunks
        :param embeddings: Embeddings array (2D, shape: [num_chunks, embedding_dim])
        """
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        
        if len(chunks) != embeddings.shape[0]:
            self.logger.error(
                f"Chunks and embeddings count mismatch: {len(chunks)} vs {embeddings.shape[0]}"
            )
            raise ValueError(
                f"Chunks and embeddings count mismatch: {len(chunks)} vs {embeddings.shape[0]}"
            )
        
        file_path = str(Path(file_path).resolve())
        
        self.logger.debug(f"Adding embeddings for file: {file_path} ({len(chunks)} chunks)")
        
        self.remove_file_embeddings(file_path)
        
        if self._embeddings is None:
            self._embeddings = embeddings
            embedding_dim = embeddings.shape[1]
        else:
            embedding_dim = self._embeddings.shape[1]
            if embeddings.shape[1] != embedding_dim:
                self.logger.error(
                    f"Embedding dimension mismatch: expected {embedding_dim}, got {embeddings.shape[1]}"
                )
                raise ValueError(
                    f"Embedding dimension mismatch: expected {embedding_dim}, got {embeddings.shape[1]}"
                )
            self._embeddings = np.vstack([self._embeddings, embeddings])
        
        for i, chunk in enumerate(chunks):
            self._metadata.append({
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "chunk_index": i,
                "chunk_text": chunk,
            })
        
        self._save_search_data()
        self.logger.info(
            f"Added {len(chunks)} chunks to search index for: {Path(file_path).name}"
        )
    
    def remove_file_embeddings(self, file_path: str) -> None:
        """
        Remove all embeddings for a file from the search index.
        
        :param file_path: Path to the file
        """
        file_path = str(Path(file_path).resolve())
        
        indices_to_remove = [
            i for i, meta in enumerate(self._metadata)
            if meta["file_path"] == file_path
        ]
        
        if not indices_to_remove:
            self.logger.debug(f"No embeddings found to remove for: {file_path}")
            return
        
        self.logger.debug(f"Removing {len(indices_to_remove)} chunks for: {file_path}")
        
        indices_to_keep = [i for i in range(len(self._metadata)) if i not in indices_to_remove]
        
        if indices_to_keep:
            self._metadata = [self._metadata[i] for i in indices_to_keep]
            if self._embeddings is not None:
                self._embeddings = self._embeddings[indices_to_keep]
        else:
            self._metadata = []
            self._embeddings = None
        
        self._save_search_data()
        self.logger.info(f"Removed embeddings for: {Path(file_path).name}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
    ) -> List[SearchResult]:
        """
        Search for similar chunks using cosine similarity.
        
        :param query_embedding: Query embedding vector (1D array)
        :param top_k: Number of top results to return (must be > 0)
        :returns: List of SearchResult objects sorted by similarity (highest first)
        """
        if top_k <= 0:
            self.logger.error(f"top_k must be positive, got: {top_k}")
            raise ValueError(f"top_k must be positive, got: {top_k}")
        
        if self._embeddings is None or len(self._embeddings) == 0:
            self.logger.warning("No embeddings in search index")
            return []
        
        if len(query_embedding.shape) > 1:
            query_embedding = query_embedding.flatten()
        
        if query_embedding.shape[0] != self._embeddings.shape[1]:
            self.logger.error(
                f"Query embedding dimension mismatch: expected {self._embeddings.shape[1]}, "
                f"got {query_embedding.shape[0]}"
            )
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self._embeddings.shape[1]}, "
                f"got {query_embedding.shape[0]}"
            )
        
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            self.logger.warning("Query embedding has zero norm")
            return []
        
        query_normalized = query_embedding / query_norm
        
        embeddings_norm = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        embeddings_normalized = self._embeddings / (embeddings_norm + 1e-8)
        
        similarities = np.dot(embeddings_normalized, query_normalized)
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            meta = self._metadata[idx]
            results.append(SearchResult(
                file_path=meta["file_path"],
                chunk_index=meta["chunk_index"],
                chunk_text=meta["chunk_text"],
                similarity_score=float(similarities[idx]),
                file_name=meta.get("file_name"),
            ))
        
        self.logger.info(f"Search completed: {len(results)} results")
        return results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the search index.
        
        :returns: Dictionary with search index statistics
        """
        if self._embeddings is None:
            return {
                "total_chunks": 0,
                "embedding_dimension": None,
                "unique_files": 0,
            }
        
        unique_files = len(set(meta["file_path"] for meta in self._metadata))
        
        return {
            "total_chunks": len(self._metadata),
            "embedding_dimension": self._embeddings.shape[1] if len(self._embeddings.shape) > 1 else None,
            "unique_files": unique_files,
        }

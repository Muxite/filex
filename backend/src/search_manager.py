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
    IMAGE_SEARCH_INDEX_NAME = "image_search_index.npy"
    IMAGE_SEARCH_METADATA_NAME = "image_search_metadata.json"
    
    def __init__(self, repository: Repository):
        """
        Initialize search manager with repository.
        
        Supports separate indices for text (768 dims) and image (512 dims) embeddings.
        
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
        self.image_search_index_path = self.index_dir / self.IMAGE_SEARCH_INDEX_NAME
        self.image_search_metadata_path = self.index_dir / self.IMAGE_SEARCH_METADATA_NAME
        
        self._embeddings: Optional[np.ndarray] = None
        self._metadata: List[Dict[str, Any]] = []
        self._image_embeddings: Optional[np.ndarray] = None
        self._image_metadata: List[Dict[str, Any]] = []
        self._load_search_data()
        
        self.logger.info("SearchManager initialized")
    
    def _load_search_data(self) -> None:
        """
        Load search index and metadata from disk for both text and images.
        """
        if self.search_index_path.exists() and self.search_metadata_path.exists():
            try:
                self._embeddings = np.load(self.search_index_path)
                with open(self.search_metadata_path, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
                self.logger.info(
                    f"Loaded text search index: {len(self._metadata)} chunks, "
                    f"embeddings shape: {self._embeddings.shape}"
                )
            except Exception as e:
                self.logger.warning(f"Failed to load text search data: {e}, starting fresh")
                self._embeddings = None
                self._metadata = []
        else:
            self._embeddings = None
            self._metadata = []
            self.logger.debug("No existing text search index found, starting fresh")
        
        if self.image_search_index_path.exists() and self.image_search_metadata_path.exists():
            try:
                self._image_embeddings = np.load(self.image_search_index_path)
                with open(self.image_search_metadata_path, 'r', encoding='utf-8') as f:
                    self._image_metadata = json.load(f)
                self.logger.info(
                    f"Loaded image search index: {len(self._image_metadata)} images, "
                    f"embeddings shape: {self._image_embeddings.shape}"
                )
            except Exception as e:
                self.logger.warning(f"Failed to load image search data: {e}, starting fresh")
                self._image_embeddings = None
                self._image_metadata = []
        else:
            self._image_embeddings = None
            self._image_metadata = []
            self.logger.debug("No existing image search index found, starting fresh")
    
    def _save_search_data(self) -> None:
        """
        Save search index and metadata to disk for both text and images.
        """
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        if self._embeddings is not None and len(self._embeddings) > 0:
            np.save(self.search_index_path, self._embeddings)
            with open(self.search_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, indent=2, ensure_ascii=False)
            self.logger.debug(
                f"Saved text search index: {len(self._metadata)} chunks, "
                f"embeddings shape: {self._embeddings.shape}"
            )
        else:
            self.logger.debug("No text search data to save")
        
        if self._image_embeddings is not None and len(self._image_embeddings) > 0:
            np.save(self.image_search_index_path, self._image_embeddings)
            with open(self.image_search_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self._image_metadata, f, indent=2, ensure_ascii=False)
            self.logger.debug(
                f"Saved image search index: {len(self._image_metadata)} images, "
                f"embeddings shape: {self._image_embeddings.shape}"
            )
        else:
            self.logger.debug("No image search data to save")
    
    def add_file_embeddings(
        self,
        file_path: str,
        chunks: List[str],
        embeddings: np.ndarray,
        is_image: bool = False,
    ) -> None:
        """
        Add or update embeddings for a file in the search index.
        
        Removes old embeddings for the file if they exist, then adds new ones.
        Supports separate indices for text (768 dims) and image (512 dims) embeddings.
        Updates search data immediately.
        
        :param file_path: Path to the file
        :param chunks: List of text chunks or image paths
        :param embeddings: Embeddings array (2D, shape: [num_chunks, embedding_dim])
        :param is_image: Whether these are image embeddings (default: False, auto-detect)
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
        
        if not is_image:
            file_ext = Path(file_path).suffix.lower()
            is_image = file_ext in {'.png', '.jpg', '.jpeg'}
        
        target_embeddings = self._image_embeddings if is_image else self._embeddings
        target_metadata = self._image_metadata if is_image else self._metadata
        
        self.logger.debug(
            f"Adding {'image' if is_image else 'text'} embeddings for file: {file_path} ({len(chunks)} chunks)"
        )
        
        self.remove_file_embeddings(file_path, is_image=is_image)
        
        if target_embeddings is None:
            if is_image:
                self._image_embeddings = embeddings
                embedding_dim = embeddings.shape[1]
            else:
                self._embeddings = embeddings
                embedding_dim = embeddings.shape[1]
        else:
            embedding_dim = target_embeddings.shape[1]
            if embeddings.shape[1] != embedding_dim:
                self.logger.error(
                    f"Embedding dimension mismatch: expected {embedding_dim}, got {embeddings.shape[1]}"
                )
                raise ValueError(
                    f"Embedding dimension mismatch: expected {embedding_dim}, got {embeddings.shape[1]}"
                )
            if is_image:
                self._image_embeddings = np.vstack([self._image_embeddings, embeddings])
            else:
                self._embeddings = np.vstack([self._embeddings, embeddings])
        
        for i, chunk in enumerate(chunks):
            metadata_entry = {
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "chunk_index": i,
                "chunk_text": chunk,
            }
            if is_image:
                self._image_metadata.append(metadata_entry)
            else:
                self._metadata.append(metadata_entry)
        
        self._save_search_data()
        self.logger.info(
            f"Added {len(chunks)} chunks to {'image' if is_image else 'text'} search index for: {Path(file_path).name}"
        )
    
    def remove_file_embeddings(self, file_path: str, is_image: Optional[bool] = None) -> None:
        """
        Remove all embeddings for a file from the search index.
        
        :param file_path: Path to the file
        :param is_image: Whether to remove from image index (None = remove from both)
        """
        file_path = str(Path(file_path).resolve())
        
        removed_text = False
        removed_image = False
        
        if is_image is None or is_image is False:
            indices_to_remove = [
                i for i, meta in enumerate(self._metadata)
                if meta["file_path"] == file_path
            ]
            
            if indices_to_remove:
                indices_to_keep = [i for i in range(len(self._metadata)) if i not in indices_to_remove]
                if indices_to_keep:
                    self._metadata = [self._metadata[i] for i in indices_to_keep]
                    if self._embeddings is not None:
                        self._embeddings = self._embeddings[indices_to_keep]
                else:
                    self._metadata = []
                    self._embeddings = None
                removed_text = True
        
        if is_image is None or is_image is True:
            image_indices_to_remove = [
                i for i, meta in enumerate(self._image_metadata)
                if meta["file_path"] == file_path
            ]
            
            if image_indices_to_remove:
                image_indices_to_keep = [i for i in range(len(self._image_metadata)) if i not in image_indices_to_remove]
                if image_indices_to_keep:
                    self._image_metadata = [self._image_metadata[i] for i in image_indices_to_keep]
                    if self._image_embeddings is not None:
                        self._image_embeddings = self._image_embeddings[image_indices_to_keep]
                else:
                    self._image_metadata = []
                    self._image_embeddings = None
                removed_image = True
        
        if removed_text or removed_image:
            self._save_search_data()
            self.logger.info(f"Removed embeddings for: {Path(file_path).name}")
        else:
            self.logger.debug(f"No embeddings found to remove for: {file_path}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        image_query_embedding: Optional[np.ndarray] = None,
    ) -> List[SearchResult]:
        """
        Search for similar chunks using cosine similarity.
        Searches both text and image indices and combines results.
        
        :param query_embedding: Query embedding vector for text search (1D array, 768 dims)
        :param top_k: Number of top results to return (must be > 0)
        :param image_query_embedding: Optional query embedding for image search (1D array, 512 dims)
        :returns: List of SearchResult objects sorted by similarity (highest first)
        """
        if top_k <= 0:
            self.logger.error(f"top_k must be positive, got: {top_k}")
            raise ValueError(f"top_k must be positive, got: {top_k}")
        
        all_results = []
        
        if self._embeddings is not None and len(self._embeddings) > 0:
            if len(query_embedding.shape) > 1:
                query_embedding = query_embedding.flatten()
            
            if query_embedding.shape[0] == self._embeddings.shape[1]:
                query_norm = np.linalg.norm(query_embedding)
                if query_norm > 0:
                    query_normalized = query_embedding / query_norm
                    embeddings_norm = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
                    embeddings_normalized = self._embeddings / (embeddings_norm + 1e-8)
                    similarities = np.dot(embeddings_normalized, query_normalized)
                    
                    for idx in range(len(self._metadata)):
                        meta = self._metadata[idx]
                        all_results.append(SearchResult(
                            file_path=meta["file_path"],
                            chunk_index=meta["chunk_index"],
                            chunk_text=meta["chunk_text"],
                            similarity_score=float(similarities[idx]),
                            file_name=meta.get("file_name"),
                        ))
        
        if image_query_embedding is not None and self._image_embeddings is not None and len(self._image_embeddings) > 0:
            if len(image_query_embedding.shape) > 1:
                image_query_embedding = image_query_embedding.flatten()
            
            if image_query_embedding.shape[0] == self._image_embeddings.shape[1]:
                query_norm = np.linalg.norm(image_query_embedding)
                if query_norm > 0:
                    query_normalized = image_query_embedding / query_norm
                    embeddings_norm = np.linalg.norm(self._image_embeddings, axis=1, keepdims=True)
                    embeddings_normalized = self._image_embeddings / (embeddings_norm + 1e-8)
                    similarities = np.dot(embeddings_normalized, query_normalized)
                    
                    for idx in range(len(self._image_metadata)):
                        meta = self._image_metadata[idx]
                        all_results.append(SearchResult(
                            file_path=meta["file_path"],
                            chunk_index=meta["chunk_index"],
                            chunk_text=meta["chunk_text"],
                            similarity_score=float(similarities[idx]),
                            file_name=meta.get("file_name"),
                        ))
        
        all_results.sort(key=lambda x: x.similarity_score, reverse=True)
        results = all_results[:top_k]
        
        self.logger.info(f"Search completed: {len(results)} results (text: {len([r for r in results if not Path(r.file_path).suffix.lower() in {'.png', '.jpg', '.jpeg'}])}, images: {len([r for r in results if Path(r.file_path).suffix.lower() in {'.png', '.jpg', '.jpeg'}])})")
        return results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the search index (text and image).
        
        :returns: Dictionary with search index statistics
        """
        text_chunks = len(self._metadata) if self._metadata else 0
        text_embedding_dim = self._embeddings.shape[1] if self._embeddings is not None and len(self._embeddings.shape) > 1 else None
        text_unique_files = len(set(meta["file_path"] for meta in self._metadata)) if self._metadata else 0
        
        image_chunks = len(self._image_metadata) if self._image_metadata else 0
        image_embedding_dim = self._image_embeddings.shape[1] if self._image_embeddings is not None and len(self._image_embeddings.shape) > 1 else None
        image_unique_files = len(set(meta["file_path"] for meta in self._image_metadata)) if self._image_metadata else 0
        
        return {
            "total_chunks": text_chunks + image_chunks,
            "embedding_dimension": text_embedding_dim,
            "unique_files": text_unique_files + image_unique_files,
        }

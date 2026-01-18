"""
Storage management for embeddings and metadata in repository.
"""
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import numpy as np

from .repository import Repository
from .logger import get_logger


class StorageManager:
    """
    Manages storage of embeddings and metadata in repository directories.
    
    Stores embeddings as numpy arrays and metadata as JSON files.
    """
    
    def __init__(self, repository: Repository):
        """
        Initialize storage manager with repository.
        
        :param repository: Repository instance (must not be None)
        """
        self.logger = get_logger(__name__)
        
        if repository is None:
            self.logger.error("repository cannot be None")
            raise ValueError("repository cannot be None")
        
        self.repository = repository
        self.embeddings_dir = repository.config.embeddings_dir
        self.metadata_dir = repository.config.metadata_dir
        
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("StorageManager initialized")
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        Generate a hash-based filename for storage.
        
        :param file_path: Original file path
        :returns: Hash string for filename
        """
        import hashlib
        return hashlib.sha256(file_path.encode()).hexdigest()
    
    def _get_embeddings_path(self, file_path: str) -> Path:
        """
        Get path for storing embeddings.
        
        :param file_path: Original file path
        :returns: Path to embeddings file
        """
        file_hash = self._get_file_hash(file_path)
        return self.embeddings_dir / f"{file_hash}.npy"
    
    def _get_metadata_path(self, file_path: str) -> Path:
        """
        Get path for storing metadata.
        
        :param file_path: Original file path
        :returns: Path to metadata file
        """
        file_hash = self._get_file_hash(file_path)
        return self.metadata_dir / f"{file_hash}.json"
    
    def save_embeddings(self, file_path: str, embeddings: np.ndarray) -> Path:
        """
        Save embeddings to disk.
        
        :param file_path: Original file path
        :param embeddings: Embeddings array to save
        :returns: Path where embeddings were saved
        """
        embeddings_path = self._get_embeddings_path(file_path)
        
        np.save(embeddings_path, embeddings)
        
        self.logger.debug(
            f"Saved embeddings: {embeddings.shape} -> {embeddings_path.name}"
        )
        return embeddings_path
    
    def load_embeddings(self, file_path: str) -> Optional[np.ndarray]:
        """
        Load embeddings from disk.
        
        :param file_path: Original file path
        :returns: Embeddings array if found, None otherwise
        """
        embeddings_path = self._get_embeddings_path(file_path)
        
        if not embeddings_path.exists():
            self.logger.debug(f"Embeddings not found: {embeddings_path.name}")
            return None
        
        embeddings = np.load(embeddings_path)
        self.logger.debug(f"Loaded embeddings: {embeddings.shape} from {embeddings_path.name}")
        return embeddings
    
    def save_metadata(self, file_path: str, metadata: Dict[str, Any]) -> Path:
        """
        Save metadata to disk as JSON.
        
        :param file_path: Original file path
        :param metadata: Metadata dictionary to save
        :returns: Path where metadata was saved
        """
        metadata_path = self._get_metadata_path(file_path)
        
        serializable_metadata = self._make_json_serializable(metadata)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.debug(f"Saved metadata to: {metadata_path.name}")
        return metadata_path
    
    def load_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load metadata from disk.
        
        :param file_path: Original file path
        :returns: Metadata dictionary if found, None otherwise
        """
        metadata_path = self._get_metadata_path(file_path)
        
        if not metadata_path.exists():
            self.logger.debug(f"Metadata not found: {metadata_path.name}")
            return None
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        self.logger.debug(f"Loaded metadata from: {metadata_path.name}")
        return metadata
    
    def _make_json_serializable(self, data: Any) -> Any:
        """
        Convert data to JSON-serializable format.
        
        :param data: Data to serialize
        :returns: JSON-serializable data
        """
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, (np.integer, np.floating)):
            return float(data)
        elif isinstance(data, dict):
            return {k: self._make_json_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._make_json_serializable(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self._make_json_serializable(item) for item in data)
        return data
    
    def save_processing_result(
        self,
        file_path: str,
        result: Dict[str, Any],
        embeddings: Optional[np.ndarray] = None
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Save both embeddings and metadata from processing result.
        
        :param file_path: Original file path
        :param result: Processing result dictionary
        :param embeddings: Embeddings array (if None, extracted from result)
        :returns: Tuple of (embeddings_path, metadata_path)
        """
        embeddings_path = None
        metadata_path = None
        
        if embeddings is None and "embeddings" in result:
            embeddings_data = result["embeddings"]
            if isinstance(embeddings_data, dict) and "embeddings" in embeddings_data:
                embeddings = embeddings_data["embeddings"]
        
        if embeddings is not None:
            embeddings_path = self.save_embeddings(file_path, embeddings)
        
        metadata = result.get("metadata", {})
        if result.get("embeddings") and isinstance(result["embeddings"], dict):
            metadata["embeddings_info"] = {
                "num_chunks": result["embeddings"].get("num_chunks"),
                "embedding_dimension": result["embeddings"].get("embedding_dimension"),
            }
        metadata["processed"] = result.get("processed", False)
        
        metadata_path = self.save_metadata(file_path, metadata)
        
        return embeddings_path, metadata_path
    
    def delete_file_data(self, file_path: str) -> None:
        """
        Delete stored data for a file.
        
        :param file_path: Original file path
        """
        embeddings_path = self._get_embeddings_path(file_path)
        metadata_path = self._get_metadata_path(file_path)
        
        deleted = False
        if embeddings_path.exists():
            embeddings_path.unlink()
            deleted = True
            self.logger.debug(f"Deleted embeddings: {embeddings_path.name}")
        
        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True
            self.logger.debug(f"Deleted metadata: {metadata_path.name}")
        
        if deleted:
            self.logger.info(f"Deleted stored data for: {file_path}")
        else:
            self.logger.debug(f"No stored data found to delete for: {file_path}")
    
    def get_storage_size(self) -> Dict[str, int]:
        """
        Get total storage size used by embeddings and metadata.
        
        :returns: Dictionary with size information in bytes
        """
        embeddings_size = sum(
            f.stat().st_size
            for f in self.embeddings_dir.glob("*.npy")
            if f.is_file()
        )
        
        metadata_size = sum(
            f.stat().st_size
            for f in self.metadata_dir.glob("*.json")
            if f.is_file()
        )
        
        return {
            "embeddings_bytes": embeddings_size,
            "metadata_bytes": metadata_size,
            "total_bytes": embeddings_size + metadata_size,
        }

"""
Repository manager that coordinates indexing and file tracking.
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np
from tqdm import tqdm

from .repository import Repository
from .index_manager import IndexManager, FileIndexEntry
from .storage_manager import StorageManager
from .search_manager import SearchManager
from .file_processor import FileProcessorRouter
from .logger import get_logger


class RepositoryManager:
    """
    Main manager for repository operations.
    
    Coordinates indexing, change detection, and storage management.
    Similar to git, provides commands for indexing and reindexing files.
    """
    
    def __init__(
        self,
        start_path: Optional[str] = None,
        processor: Optional[FileProcessorRouter] = None,
        create: bool = True,
    ):
        """
        Initialize repository manager.
        
        :param start_path: Path to start repository search from (defaults to current directory)
        :param processor: FileProcessorRouter instance (optional)
        :param create: Whether to create repository if not found
        """
        self.logger = get_logger(__name__)
        
        self.repository = Repository(start_path=start_path, create=create)
        self.index_manager = IndexManager(self.repository)
        self.storage_manager = StorageManager(self.repository)
        self.search_manager = SearchManager(self.repository)
        self.processor = processor
        
        self.logger.info("RepositoryManager initialized")
    
    def set_processor(self, processor: FileProcessorRouter) -> None:
        """
        Set or update the file processor router.
        
        :param processor: FileProcessorRouter instance (must not be None)
        """
        if processor is None:
            self.logger.error("processor cannot be None")
            raise ValueError("processor cannot be None")
        
        self.processor = processor
        self.logger.info("File processor router updated")
    
    def index_file(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """
        Index a single file.
        
        :param file_path: Path to file to index
        :param force: Force reindexing even if file hasn't changed
        :returns: Dictionary with indexing result
        """
        if self.processor is None:
            raise ValueError("FileProcessorRouter not set. Call set_processor() first.")
        
        file_path = Path(file_path).resolve()
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not self.repository.is_path_in_repo(str(file_path)):
            self.logger.warning(f"File outside repository: {file_path}")
        
        from .file_metadata import FileMetadata
        metadata = FileMetadata.from_path(str(file_path))
        
        if not force and not self.index_manager.has_changed(metadata):
            self.logger.info(f"File unchanged, skipping: {metadata.file_name}")
            entry = self.index_manager.get_index_entry(str(file_path))
            return {
                "file_path": str(file_path),
                "indexed": False,
                "reason": "File has not changed since last indexing",
                "entry": entry.to_dict() if entry else None,
            }
        
        self.logger.info(f"Indexing file: {metadata.file_name}")
        
        result = self.processor.process_file(str(file_path))
        
        file_hash = IndexManager.compute_file_hash(str(file_path))
        
        num_chunks = None
        embedding_dimension = None
        if result.get("embeddings") and isinstance(result["embeddings"], dict):
            num_chunks = result["embeddings"].get("num_chunks")
            embedding_dimension = result["embeddings"].get("embedding_dimension")
        
        self.index_manager.add_entry(
            metadata=metadata,
            file_hash=file_hash,
            num_chunks=num_chunks,
            embedding_dimension=embedding_dimension,
        )
        
        if result.get("processed", False):
            embeddings = None
            chunks = None
            if "embeddings" in result and isinstance(result["embeddings"], dict):
                embeddings = result["embeddings"].get("embeddings")
                chunks = result["embeddings"].get("chunks")
            
            if embeddings is not None:
                self.storage_manager.save_processing_result(
                    str(file_path),
                    result,
                    embeddings=embeddings,
                )
                
                if chunks is not None and isinstance(chunks, list) and len(chunks) > 0:
                    if isinstance(embeddings, np.ndarray):
                        self.logger.info(
                            f"Adding {len(chunks)} chunks to search index for: {Path(file_path).name}"
                        )
                        try:
                            self.search_manager.add_file_embeddings(
                                str(file_path),
                                chunks,
                                embeddings,
                            )
                        except Exception as e:
                            self.logger.error(
                                f"Failed to add embeddings to search index for {Path(file_path).name}: {e}",
                                exc_info=True
                            )
                    else:
                        self.logger.warning(
                            f"Embeddings for {Path(file_path).name} are not numpy array, "
                            f"type: {type(embeddings)}"
                        )
                else:
                    if result.get("processed", False):
                        self.logger.warning(
                            f"No chunks found for {Path(file_path).name}, "
                            f"chunks type: {type(chunks)}, chunks value: {chunks}"
                        )
        
        return {
            "file_path": str(file_path),
            "indexed": True,
            "processed": result.get("processed", False),
            "metadata": result.get("metadata"),
            "num_chunks": num_chunks,
            "embedding_dimension": embedding_dimension,
        }
    
    def index_directory(
        self,
        directory: Optional[str] = None,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Index all files in a directory.
        
        :param directory: Directory to index (defaults to repository root)
        :param recursive: Whether to recursively index subdirectories
        :param extensions: List of extensions to include (None = all)
        :param force: Force reindexing even if files haven't changed
        :returns: Dictionary with indexing statistics
        """
        if directory is None:
            directory = self.repository.get_work_tree_root()
        
        directory = Path(directory).resolve()
        
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory not found: {directory}")
        
        if not self.repository.is_path_in_repo(str(directory)):
            self.logger.warning(f"Directory outside repository: {directory}")
        
        self.logger.info(f"Indexing directory: {directory} (recursive: {recursive})")
        
        files_to_index = []
        
        if recursive:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    if ".filex" in file_path.parts:
                        continue
                    if extensions is None or file_path.suffix.lower() in [e.lower() for e in extensions]:
                        files_to_index.append(file_path)
        else:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    if ".filex" in file_path.parts:
                        continue
                    if extensions is None or file_path.suffix.lower() in [e.lower() for e in extensions]:
                        files_to_index.append(file_path)
        
        files_to_index = sorted(set(files_to_index), key=str)
        
        self.logger.info(f"Found {len(files_to_index)} file(s) to index")
        
        indexed_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        with tqdm(total=len(files_to_index), desc="Indexing files", unit="file") as pbar:
            for file_path in files_to_index:
                try:
                    pbar.set_description(f"Indexing: {file_path.name}")
                    result = self.index_file(str(file_path), force=force)
                    if result.get("indexed"):
                        indexed_count += 1
                        pbar.set_postfix({"indexed": indexed_count, "skipped": skipped_count})
                    else:
                        skipped_count += 1
                        pbar.set_postfix({"indexed": indexed_count, "skipped": skipped_count})
                except Exception as e:
                    error_count += 1
                    error_msg = f"{file_path}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(f"Error indexing {file_path}: {e}", exc_info=True)
                    pbar.set_postfix({"indexed": indexed_count, "errors": error_count})
                finally:
                    pbar.update(1)
        
        stats = {
            "total_files": len(files_to_index),
            "indexed": indexed_count,
            "skipped": skipped_count,
            "errors": error_count,
            "error_messages": errors,
        }
        
        self.logger.info(
            f"Directory indexing completed: {indexed_count} indexed, "
            f"{skipped_count} skipped, {error_count} errors"
        )
        
        return stats
    
    def reindex_all(self, force: bool = True) -> Dict[str, Any]:
        """
        Reindex all files in the repository.
        
        :param force: Force reindexing even if files haven't changed
        :returns: Dictionary with reindexing statistics
        """
        self.logger.info("Reindexing all files in repository")
        
        work_tree = self.repository.get_work_tree_root()
        return self.index_directory(directory=str(work_tree), recursive=True, force=force)
    
    def get_index_status(self) -> Dict[str, Any]:
        """
        Get status of the index.
        
        :returns: Dictionary with index statistics
        """
        entries = self.index_manager.get_all_entries()
        storage_size = self.storage_manager.get_storage_size()
        
        text_files = sum(1 for e in entries if e.is_text_type)
        non_text_files = len(entries) - text_files
        
        total_chunks = sum(e.num_chunks or 0 for e in entries if e.is_text_type)
        
        return {
            "total_indexed_files": len(entries),
            "text_files": text_files,
            "non_text_files": non_text_files,
            "total_chunks": total_chunks,
            "storage_size": storage_size,
            "repository_path": str(self.repository.repo_path),
            "work_tree_root": str(self.repository.get_work_tree_root()),
        }
    
    def list_indexed_files(self, extension: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all indexed files.
        
        :param extension: Filter by extension (optional)
        :returns: List of indexed file dictionaries
        """
        entries = self.index_manager.get_all_entries()
        
        if extension:
            entries = [e for e in entries if e.extension.lower() == extension.lower()]
        
        return [e.to_dict() for e in entries]

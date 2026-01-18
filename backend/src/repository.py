"""
Repository management for FileX index tracking.
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .logger import get_logger


@dataclass
class RepositoryConfig:
    """
    Configuration for a FileX repository.
    """
    repo_path: Path
    index_dir: Path
    embeddings_dir: Path
    metadata_dir: Path
    index_db_path: Path


class Repository:
    """
    Manages a FileX repository in a .filex directory.
    
    Similar to git, finds or creates a .filex folder by walking up
    the directory tree from the current working directory.
    """
    
    REPO_DIR_NAME = ".filex"
    INDEX_DIR_NAME = "index"
    EMBEDDINGS_DIR_NAME = "embeddings"
    METADATA_DIR_NAME = "metadata"
    INDEX_DB_NAME = "index.db"
    
    def __init__(self, start_path: Optional[str] = None, create: bool = True):
        """
        Initialize repository, finding or creating .filex folder.
        
        :param start_path: Path to start searching from (defaults to current directory)
        :param create: Whether to create repository if not found
        """
        self.logger = get_logger(__name__)
        
        if start_path is None:
            start_path = os.getcwd()
        
        start_path = Path(start_path).resolve()
        self.logger.debug(f"Searching for repository starting from: {start_path}")
        
        repo_path = self.find_repository(start_path)
        
        if repo_path is None and create:
            repo_path = self.create_repository(start_path)
        elif repo_path is None:
            raise FileNotFoundError(
                f"No .filex repository found starting from {start_path}. "
                "Run with create=True to create one."
            )
        
        self.repo_path = repo_path
        self.config = self._setup_config()
        self.logger.info(f"Repository initialized at: {self.repo_path}")
    
    @classmethod
    def find_repository(cls, start_path: Path) -> Optional[Path]:
        """
        Walk up directory tree to find .filex folder.
        
        :param start_path: Path to start searching from
        :returns: Path to .filex folder if found, None otherwise
        """
        logger = get_logger(__name__)
        current = start_path.resolve()
        
        while True:
            repo_path = current / cls.REPO_DIR_NAME
            if repo_path.exists() and repo_path.is_dir():
                logger.debug(f"Found repository at: {repo_path}")
                return repo_path
            
            parent = current.parent
            if parent == current:
                logger.debug(f"No repository found, reached filesystem root")
                break
            
            current = parent
        
        return None
    
    def create_repository(self, location: Path) -> Path:
        """
        Create a new .filex repository at the given location.
        
        :param location: Location to create repository
        :returns: Path to created repository
        """
        repo_path = location / self.REPO_DIR_NAME
        
        if repo_path.exists():
            self.logger.warning(f"Repository already exists at: {repo_path}")
            return repo_path
        
        self.logger.info(f"Creating new repository at: {repo_path}")
        repo_path.mkdir(parents=True, exist_ok=True)
        
        index_dir = repo_path / self.INDEX_DIR_NAME
        embeddings_dir = repo_path / self.EMBEDDINGS_DIR_NAME
        metadata_dir = repo_path / self.METADATA_DIR_NAME
        
        for directory in [index_dir, embeddings_dir, metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created directory: {directory}")
        
        self.logger.info(f"Repository created successfully at: {repo_path}")
        return repo_path
    
    def _setup_config(self) -> RepositoryConfig:
        """
        Set up repository directory structure and paths.
        
        :returns: RepositoryConfig with all paths configured
        """
        index_dir = self.repo_path / self.INDEX_DIR_NAME
        embeddings_dir = self.repo_path / self.EMBEDDINGS_DIR_NAME
        metadata_dir = self.repo_path / self.METADATA_DIR_NAME
        index_db_path = index_dir / self.INDEX_DB_NAME
        
        return RepositoryConfig(
            repo_path=self.repo_path,
            index_dir=index_dir,
            embeddings_dir=embeddings_dir,
            metadata_dir=metadata_dir,
            index_db_path=index_db_path,
        )
    
    def get_work_tree_root(self) -> Path:
        """
        Get the root of the working tree (parent of .filex folder).
        
        :returns: Path to working tree root
        """
        return self.repo_path.parent
    
    def is_path_in_repo(self, file_path: str) -> bool:
        """
        Check if a file path is within the repository working tree.
        
        :param file_path: Path to check
        :returns: True if path is within repository
        """
        try:
            file_path = Path(file_path).resolve()
            work_tree = self.get_work_tree_root()
            return str(file_path).startswith(str(work_tree))
        except Exception:
            return False

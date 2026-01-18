"""
Index management for tracking indexed files and detecting changes.
"""
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .repository import Repository
from .file_metadata import FileMetadata
from .logger import get_logger


class FileIndexEntry:
    """
    Represents an entry in the file index.
    """
    def __init__(
        self,
        file_path: str,
        file_hash: str,
        file_size: int,
        modified_time: datetime,
        indexed_time: datetime,
        extension: str,
        is_text_type: bool,
        num_chunks: Optional[int] = None,
        embedding_dimension: Optional[int] = None,
    ):
        self.file_path = file_path
        self.file_hash = file_hash
        self.file_size = file_size
        self.modified_time = modified_time
        self.indexed_time = indexed_time
        self.extension = extension
        self.is_text_type = is_text_type
        self.num_chunks = num_chunks
        self.embedding_dimension = embedding_dimension
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert index entry to dictionary.
        
        :returns: Dictionary representation
        """
        return {
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "modified_time": self.modified_time.isoformat() if self.modified_time else None,
            "indexed_time": self.indexed_time.isoformat() if self.indexed_time else None,
            "extension": self.extension,
            "is_text_type": self.is_text_type,
            "num_chunks": self.num_chunks,
            "embedding_dimension": self.embedding_dimension,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "FileIndexEntry":
        """
        Create FileIndexEntry from database row.
        
        :param row: Database row tuple
        :returns: FileIndexEntry instance
        """
        return cls(
            file_path=row[0],
            file_hash=row[1],
            file_size=row[2],
            modified_time=datetime.fromisoformat(row[3]) if row[3] else None,
            indexed_time=datetime.fromisoformat(row[4]) if row[4] else None,
            extension=row[5],
            is_text_type=bool(row[6]),
            num_chunks=row[7],
            embedding_dimension=row[8],
        )


class IndexManager:
    """
    Manages the file index database and tracks indexed files.
    
    Detects changes by comparing file hashes, sizes, and modification times.
    """
    
    def __init__(self, repository: Repository):
        """
        Initialize index manager with repository.
        
        :param repository: Repository instance (must not be None)
        """
        self.logger = get_logger(__name__)
        
        if repository is None:
            self.logger.error("repository cannot be None")
            raise ValueError("repository cannot be None")
        
        self.repository = repository
        self.db_path = repository.config.index_db_path
        self._init_database()
        self.logger.info("IndexManager initialized")
    
    def _init_database(self) -> None:
        """
        Initialize the index database with schema.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_index (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                modified_time TEXT NOT NULL,
                indexed_time TEXT NOT NULL,
                extension TEXT NOT NULL,
                is_text_type INTEGER NOT NULL,
                num_chunks INTEGER,
                embedding_dimension INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_hash ON file_index(file_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_extension ON file_index(extension)
        """)
        
        conn.commit()
        conn.close()
        self.logger.debug("Index database initialized")
    
    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """
        Compute SHA256 hash of file contents.
        
        :param file_path: Path to file
        :returns: Hex digest of file hash
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _compute_file_hash(self, file_path: str) -> str:
        """
        Compute SHA256 hash of file contents (instance method wrapper).
        
        :param file_path: Path to file
        :returns: Hex digest of file hash
        """
        return self.compute_file_hash(file_path)
    
    def is_indexed(self, file_path: str) -> bool:
        """
        Check if a file is in the index.
        
        :param file_path: Path to file
        :returns: True if file is indexed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM file_index WHERE file_path = ?", (file_path,))
        result = cursor.fetchone() is not None
        
        conn.close()
        return result
    
    def get_index_entry(self, file_path: str) -> Optional[FileIndexEntry]:
        """
        Get index entry for a file if it exists.
        
        :param file_path: Path to file
        :returns: FileIndexEntry if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM file_index WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return FileIndexEntry.from_row(row)
        return None
    
    def has_changed(self, metadata: FileMetadata) -> bool:
        """
        Check if a file has changed since last indexing.
        
        :param metadata: File metadata
        :returns: True if file has changed or is not indexed
        """
        entry = self.get_index_entry(metadata.file_path)
        
        if entry is None:
            self.logger.debug(f"File not in index: {metadata.file_name}")
            return True
        
        if entry.file_size != metadata.file_size_bytes:
            self.logger.debug(
                f"File size changed: {metadata.file_name} "
                f"({entry.file_size} -> {metadata.file_size_bytes})"
            )
            return True
        
        if entry.modified_time and metadata.modified_time:
            if entry.modified_time < metadata.modified_time:
                self.logger.debug(
                    f"File modified time changed: {metadata.file_name} "
                    f"({entry.modified_time} -> {metadata.modified_time})"
                )
                return True
        
        file_hash = self.compute_file_hash(metadata.file_path)
        if entry.file_hash != file_hash:
            self.logger.debug(
                f"File hash changed: {metadata.file_name} "
                f"({entry.file_hash[:8]}... -> {file_hash[:8]}...)"
            )
            return True
        
        return False
    
    def add_entry(
        self,
        metadata: FileMetadata,
        file_hash: str,
        num_chunks: Optional[int] = None,
        embedding_dimension: Optional[int] = None,
    ) -> None:
        """
        Add or update an entry in the index.
        
        :param metadata: File metadata
        :param file_hash: SHA256 hash of file contents
        :param num_chunks: Number of chunks (for text files)
        :param embedding_dimension: Embedding dimension (for text files)
        """
        indexed_time = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO file_index (
                file_path, file_hash, file_size, modified_time, indexed_time,
                extension, is_text_type, num_chunks, embedding_dimension
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.file_path,
            file_hash,
            metadata.file_size_bytes,
            metadata.modified_time.isoformat() if metadata.modified_time else None,
            indexed_time.isoformat(),
            metadata.file_extension,
            1 if metadata.is_text_type else 0,
            num_chunks,
            embedding_dimension,
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(
            f"Index entry added/updated: {metadata.file_name} "
            f"(hash: {file_hash[:8]}..., chunks: {num_chunks})"
        )
    
    def remove_entry(self, file_path: str) -> None:
        """
        Remove an entry from the index.
        
        :param file_path: Path to file
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM file_index WHERE file_path = ?", (file_path,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        if deleted:
            self.logger.info(f"Index entry removed: {file_path}")
        else:
            self.logger.debug(f"Index entry not found for removal: {file_path}")
    
    def get_all_entries(self) -> List[FileIndexEntry]:
        """
        Get all index entries.
        
        :returns: List of all FileIndexEntry instances
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM file_index")
        rows = cursor.fetchall()
        conn.close()
        
        return [FileIndexEntry.from_row(row) for row in rows]
    
    def get_indexed_files_count(self) -> int:
        """
        Get total number of indexed files.
        
        :returns: Number of indexed files
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM file_index")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count

"""
File metadata collection and management.
"""
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional

from .logger import get_logger


@dataclass
class FileMetadata:
    """
    Metadata about a file including type, size, and other information.
    """
    file_path: str
    file_name: str
    file_extension: str
    file_size_bytes: int
    is_text_type: bool
    modified_time: Optional[datetime] = None
    created_time: Optional[datetime] = None
    
    @classmethod
    def from_path(cls, file_path: str) -> "FileMetadata":
        """
        Create FileMetadata from a file path.
        
        :param file_path: Path to the file (must exist)
        :returns: FileMetadata instance with all file information
        """
        logger = get_logger(__name__)
        logger.debug(f"Collecting metadata for file: {file_path}")
        
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = path.stat()
        extension = path.suffix.lower()
        text_extensions = {'.txt', '.docx'}
        is_text = extension in text_extensions
        
        metadata = cls(
            file_path=str(path.resolve()),
            file_name=path.name,
            file_extension=extension,
            file_size_bytes=stat.st_size,
            is_text_type=is_text,
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            created_time=datetime.fromtimestamp(stat.st_ctime),
        )
        
        logger.info(
            f"Metadata collected: {metadata.file_name} "
            f"({metadata.file_size_kb:.2f} KB, type: {extension}, text: {is_text})"
        )
        return metadata
    
    @property
    def file_size_kb(self) -> float:
        """
        Get file size in kilobytes.
        
        :returns: File size in KB
        """
        return self.file_size_bytes / 1024
    
    @property
    def file_size_mb(self) -> float:
        """
        Get file size in megabytes.
        
        :returns: File size in MB
        """
        return self.file_size_bytes / (1024 * 1024)

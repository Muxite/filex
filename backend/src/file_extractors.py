"""
File extraction utilities for various file types.
"""
from typing import Optional
from pathlib import Path
import docx

from .logger import get_logger


class FileExtractor:
    """
    Utility class for extracting text content from files.
    """
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract text content from a file based on its extension.
        
        :param file_path: Path to the file (must exist and be readable)
        :returns: Extracted text content
        :raises FileNotFoundError: If file does not exist
        :raises ValueError: If file type is not supported
        """
        logger = get_logger(__name__)
        logger.debug(f"Extracting text from file: {file_path}")
        
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = path.suffix.lower()
        logger.debug(f"File extension: {suffix}")
        
        if suffix == '.txt':
            text = FileExtractor._extract_txt(file_path)
            logger.info(f"Successfully extracted {len(text)} characters from TXT file")
            return text
        elif suffix == '.docx':
            text = FileExtractor._extract_docx(file_path)
            logger.info(f"Successfully extracted {len(text)} characters from DOCX file")
            return text
        else:
            logger.warning(f"Unsupported file type: {suffix}")
            raise ValueError(f"Unsupported file type: {suffix}")
    
    @staticmethod
    def _extract_txt(file_path: str) -> str:
        """
        Extract text from a plain text file.
        
        :param file_path: Path to the text file (must exist and be readable)
        :returns: File content as string
        """
        logger = get_logger(__name__)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                logger.debug(f"Read TXT file with UTF-8 encoding")
                return text
        except UnicodeDecodeError:
            logger.debug(f"UTF-8 encoding failed, trying latin-1")
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    @staticmethod
    def _extract_docx(file_path: str) -> str:
        """
        Extract text from a DOCX file.
        
        :param file_path: Path to the DOCX file (must exist and be valid)
        :returns: Extracted text content
        :raises ValueError: If file is not a valid DOCX file
        """
        logger = get_logger(__name__)
        try:
            logger.debug(f"Opening DOCX file: {file_path}")
            doc = docx.Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs]
            text = '\n'.join(paragraphs)
            logger.debug(f"Extracted {len(paragraphs)} paragraphs from DOCX")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX file {file_path}: {e}")
            raise ValueError(f"Failed to extract text from DOCX file: {e}")
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get the size of a file in bytes.
        
        :param file_path: Path to the file (must exist)
        :returns: File size in bytes (always >= 0)
        """
        return Path(file_path).stat().st_size

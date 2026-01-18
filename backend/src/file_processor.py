"""
File processor router that coordinates file handling based on file type.
"""
from typing import List, Optional, Dict, Any

from .file_metadata import FileMetadata
from .file_handlers import FileHandler, TextFileHandler, DefaultFileHandler
from .image_handlers import ImageFileHandler
from .handler import TextEmbeddingHandler
from .logger import get_logger


class FileProcessorRouter:
    """
    Routes file processing to appropriate handlers based on file type.
    
    Uses dependency injection for handlers and coordinates file processing.
    """
    
    def __init__(
        self,
        text_handler: Optional[TextFileHandler] = None,
        image_handler: Optional[ImageFileHandler] = None,
        default_handler: Optional[DefaultFileHandler] = None
    ):
        """
        Initialize file processor router with handlers.
        
        :param text_handler: Handler for text files (optional, will use default if None)
        :param image_handler: Handler for image files (optional)
        :param default_handler: Handler for unsupported file types (optional, will create default if None)
        """
        self.logger = get_logger(__name__)
        self.text_handler = text_handler
        self.image_handler = image_handler
        self.default_handler = default_handler or DefaultFileHandler()
        
        self._handlers: List[FileHandler] = []
        if self.text_handler:
            self._handlers.append(self.text_handler)
            self.logger.debug("TextFileHandler registered")
        if self.image_handler:
            self._handlers.append(self.image_handler)
            self.logger.debug("ImageFileHandler registered")
        self._handlers.append(self.default_handler)
        self.logger.debug("DefaultFileHandler registered")
        self.logger.info(f"FileProcessorRouter initialized with {len(self._handlers)} handler(s)")
    
    def set_text_handler(self, text_handler: TextFileHandler) -> None:
        """
        Set or change the text file handler.
        
        :param text_handler: The text file handler (must not be None)
        """
        if text_handler is None:
            self.logger.error("text_handler cannot be None")
            raise ValueError("text_handler cannot be None")
        
        self.text_handler = text_handler
        if self.text_handler not in self._handlers:
            self._handlers.insert(0, self.text_handler)
        self.logger.info("Text file handler updated")
    
    def set_image_handler(self, image_handler: ImageFileHandler) -> None:
        """
        Set or change the image file handler.
        
        :param image_handler: The image file handler (must not be None)
        """
        if image_handler is None:
            self.logger.error("image_handler cannot be None")
            raise ValueError("image_handler cannot be None")
        
        self.image_handler = image_handler
        if self.image_handler not in self._handlers:
            insert_pos = len([h for h in self._handlers if isinstance(h, TextFileHandler)])
            self._handlers.insert(insert_pos, self.image_handler)
        self.logger.info("Image file handler updated")
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a file by collecting metadata and routing to appropriate handler.
        
        :param file_path: Path to the file (must exist)
        :returns: Dictionary with file metadata and processing results
        """
        self.logger.info(f"Processing file: {file_path}")
        metadata = FileMetadata.from_path(file_path)
        
        for handler in self._handlers:
            if handler.can_handle(metadata):
                handler_name = type(handler).__name__
                self.logger.debug(f"Routing to handler: {handler_name}")
                result = handler.process(metadata)
                self.logger.info(
                    f"File processing completed: {metadata.file_name} "
                    f"(processed: {result.get('processed', False)})"
                )
                return result
        
        self.logger.warning(f"No handler found, using default handler for: {metadata.file_name}")
        return self.default_handler.process(metadata)
    
    def get_file_metadata(self, file_path: str) -> FileMetadata:
        """
        Get file metadata without processing.
        
        :param file_path: Path to the file (must exist)
        :returns: FileMetadata instance
        """
        return FileMetadata.from_path(file_path)
    
    def process_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple files.
        
        :param file_paths: List of file paths to process
        :returns: List of processing results for each file
        """
        self.logger.info(f"Processing {len(file_paths)} file(s)")
        results = []
        for i, file_path in enumerate(file_paths, 1):
            try:
                self.logger.debug(f"Processing file {i}/{len(file_paths)}: {file_path}")
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
                results.append({
                    "error": str(e),
                    "file_path": file_path,
                    "processed": False,
                })
        
        successful = sum(1 for r in results if r.get("processed", False))
        self.logger.info(f"Batch processing completed: {successful}/{len(file_paths)} successful")
        return results

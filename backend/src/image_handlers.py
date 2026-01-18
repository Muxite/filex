"""
Image file handlers for processing image files with computer vision.
"""
from typing import Dict, Any
import numpy as np

from .file_metadata import FileMetadata
from .image_embedders import CLIPImageEmbedder
from .logger import get_logger


class ImageFileHandler:
    """
    Handler for image files (.png, .jpg) that generates embeddings using computer vision.
    
    Uses dependency injection for the image embedder.
    """
    
    def __init__(self, image_embedder: CLIPImageEmbedder):
        """
        Initialize image file handler with image embedder.
        
        :param image_embedder: The CLIPImageEmbedder to use for embeddings (must not be None)
        """
        self.logger = get_logger(__name__)
        
        if image_embedder is None:
            self.logger.error("image_embedder cannot be None")
            raise ValueError("image_embedder cannot be None")
        
        self.image_embedder = image_embedder
        self.supported_extensions = {'.png', '.jpg', '.jpeg'}
        self.logger.info("ImageFileHandler initialized")
    
    def can_handle(self, metadata: FileMetadata) -> bool:
        """
        Check if this handler can process the file.
        
        :param metadata: File metadata
        :returns: True if file is a supported image type
        """
        can_handle = metadata.is_image_type and metadata.file_extension in self.supported_extensions
        if can_handle:
            self.logger.debug(f"ImageFileHandler can handle file: {metadata.file_name}")
        return can_handle
    
    def process(self, metadata: FileMetadata) -> Dict[str, Any]:
        """
        Process image file and generate embeddings.
        
        :param metadata: File metadata (must be an image file)
        :returns: Dictionary containing metadata and embedding results
        """
        if not self.can_handle(metadata):
            self.logger.error(f"Cannot handle file type: {metadata.file_extension}")
            raise ValueError(f"Cannot handle file type: {metadata.file_extension}")
        
        self.logger.info(
            f"Processing image file: {metadata.file_name} "
            f"({metadata.file_size_kb:.2f} KB)"
        )
        
        embedding = self.image_embedder.embed(metadata.file_path)
        
        embedding_dim = embedding.shape[0] if len(embedding.shape) == 1 else embedding.shape[1]
        
        chunks = [metadata.file_path]
        embeddings = embedding.reshape(1, -1) if len(embedding.shape) == 1 else embedding
        
        self.logger.info(
            f"Successfully processed image file: {metadata.file_name} "
            f"(embedding dimension: {embedding_dim})"
        )
        
        return {
            "metadata": {
                "file_path": metadata.file_path,
                "file_name": metadata.file_name,
                "file_extension": metadata.file_extension,
                "file_size_bytes": metadata.file_size_bytes,
                "file_size_kb": metadata.file_size_kb,
                "file_size_mb": metadata.file_size_mb,
                "modified_time": metadata.modified_time.isoformat() if metadata.modified_time else None,
                "created_time": metadata.created_time.isoformat() if metadata.created_time else None,
            },
            "embeddings": {
                "chunks": chunks,
                "embeddings": embeddings,
                "num_chunks": 1,
                "embedding_dimension": embedding_dim,
            },
            "processed": True,
        }

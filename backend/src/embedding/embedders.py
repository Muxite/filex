"""
Embedder implementations.
"""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from .interfaces import Embedder
from ..logger import get_logger


class SentenceTransformerEmbedder:
    """
    Embedder implementation using sentence-transformers library.
    
    Wraps a SentenceTransformer model to provide the Embedder interface.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedder with a sentence-transformer model.
        
        :param model_name: Name of the sentence-transformer model to use (must not be empty)
        """
        self.logger = get_logger(__name__)
        
        if not model_name:
            self.logger.error("model_name cannot be empty")
            raise ValueError("model_name cannot be empty")
        
        self.logger.info(f"Loading sentence-transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.logger.info(f"SentenceTransformerEmbedder initialized with model: {model_name}")
    
    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for a single text string.
        
        :param text: The text to embed (must not be empty)
        :returns: A 1D numpy array representing the embedding vector
        :raises ValueError: If text is empty or invalid
        """
        if not text:
            self.logger.error("Cannot embed empty text")
            raise ValueError("text cannot be empty")
        
        self.logger.debug(f"Generating embedding for text of length {len(text)} characters")
        embedding = self.model.encode(text, convert_to_numpy=True)
        self.logger.debug(f"Generated embedding with dimension {embedding.shape[0]}")
        return embedding
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embedding vectors for multiple texts efficiently.
        
        :param texts: List of texts to embed (must not be empty)
        :returns: A 2D numpy array where each row is an embedding vector
        :postcondition: result.shape[0] == len(texts)
        :raises ValueError: If texts list is empty
        """
        if not texts:
            self.logger.error("Cannot embed empty batch")
            raise ValueError("texts list cannot be empty")
        
        self.logger.debug(f"Generating embeddings for batch of {len(texts)} texts")
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        self.logger.debug(
            f"Generated batch embeddings: shape {embeddings.shape}, "
            f"dimension {embeddings.shape[1] if len(embeddings.shape) > 1 else embeddings.shape[0]}"
        )
        return embeddings

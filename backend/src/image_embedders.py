"""
Image embedder implementations using computer vision models.
"""
import os
from typing import List
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

from .interfaces import Embedder
from .logger import get_logger

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


class CLIPImageEmbedder:
    """
    Image embedder implementation using CLIP (Contrastive Language-Image Pre-training).
    
    CLIP provides high-quality image embeddings that can be used for semantic
    image search. The embeddings are in the same space as text embeddings,
    enabling cross-modal search.
    """
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize the image embedder with a CLIP model.
        
        Uses computer vision models for generating image embeddings.
        Models are automatically cached by huggingface_hub.
        
        :param model_name: Name of the CLIP model to use (must not be empty)
            Default: "openai/clip-vit-base-patch32" (512 dimensions, good balance)
            Alternatives: "openai/clip-vit-large-patch14" (768 dims, higher quality)
        """
        self.logger = get_logger(__name__)
        
        if not model_name:
            self.logger.error("model_name cannot be empty")
            raise ValueError("model_name cannot be empty")
        
        self.logger.info(f"Loading CLIP model: {model_name}")
        self.logger.debug(
            "Models are automatically cached by huggingface_hub in ~/.cache/huggingface/hub/. "
            "First load downloads the model, subsequent loads use cache."
        )
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger.debug(f"Using device: {self.device}")
        
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model_name = model_name
        self.model.eval()
        
        self.logger.info(f"CLIPImageEmbedder initialized with model: {model_name} on {self.device}")
    
    def embed(self, image_path: str) -> np.ndarray:
        """
        Generate embedding vector for a single image.
        
        :param image_path: Path to the image file (must exist and be readable)
        :returns: A 1D numpy array representing the image embedding vector
        :raises ValueError: If image cannot be loaded or processed
        """
        if not image_path:
            self.logger.error("Cannot embed empty image path")
            raise ValueError("image_path cannot be empty")
        
        try:
            image = Image.open(image_path).convert("RGB")
            self.logger.debug(f"Loaded image: {image_path}, size: {image.size}")
        except Exception as e:
            self.logger.error(f"Failed to load image {image_path}: {e}")
            raise ValueError(f"Failed to load image: {e}")
        
        with torch.no_grad():
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            image_features = self.model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            embedding = image_features.cpu().numpy().flatten()
        
        self.logger.debug(f"Generated embedding with dimension {embedding.shape[0]}")
        return embedding
    
    def embed_batch(self, image_paths: List[str]) -> np.ndarray:
        """
        Generate embedding vectors for multiple images efficiently.
        
        :param image_paths: List of image file paths (must not be empty)
        :returns: A 2D numpy array where each row is an embedding vector
        :postcondition: result.shape[0] == len(image_paths)
        :raises ValueError: If image_paths list is empty
        """
        if not image_paths:
            self.logger.error("Cannot embed empty batch")
            raise ValueError("image_paths list cannot be empty")
        
        self.logger.debug(f"Generating embeddings for batch of {len(image_paths)} images")
        
        images = []
        for image_path in image_paths:
            try:
                image = Image.open(image_path).convert("RGB")
                images.append(image)
            except Exception as e:
                self.logger.error(f"Failed to load image {image_path}: {e}")
                raise ValueError(f"Failed to load image {image_path}: {e}")
        
        with torch.no_grad():
            inputs = self.processor(images=images, return_tensors="pt", padding=True).to(self.device)
            image_features = self.model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            embeddings = image_features.cpu().numpy()
        
        self.logger.debug(
            f"Generated batch embeddings: shape {embeddings.shape}, "
            f"dimension {embeddings.shape[1] if len(embeddings.shape) > 1 else embeddings.shape[0]}"
        )
        return embeddings
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for text using CLIP's text encoder.
        
        This enables cross-modal search where text queries can find images.
        
        :param text: Text string to embed
        :returns: A 1D numpy array representing the text embedding vector (same space as images)
        :raises ValueError: If text is empty
        """
        if not text:
            self.logger.error("Cannot embed empty text")
            raise ValueError("text cannot be empty")
        
        with torch.no_grad():
            inputs = self.processor(text=text, return_tensors="pt", padding=True, truncation=True).to(self.device)
            text_features = self.model.get_text_features(**inputs)
            text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
            embedding = text_features.cpu().numpy().flatten()
        
        self.logger.debug(f"Generated text embedding with dimension {embedding.shape[0]}")
        return embedding
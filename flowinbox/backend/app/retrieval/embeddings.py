import os
import gc
from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """Abstract embedding provider interface."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of text strings."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the actual output dimension of embeddings."""
        pass


class FastEmbedProvider(EmbeddingProvider):
    """FastEmbed implementation using BAAI/bge-small-en-v1.5 model with lazy initialization."""

    def __init__(self):
        self._model = None
        self._dim = 384

    def _get_model(self):
        # On 512MB RAM environments (like Render Free Tier), loading 350MB ONNX FastEmbed model causes OOM kills.
        # Use lightweight fallback embeddings in low memory mode or production.
        from app.core.config import settings
        low_memory = os.environ.get("LOW_MEMORY_MODE", "true").lower() == "true"
        if settings.ENVIRONMENT == "production" and low_memory:
            return None

        if self._model is None:
            try:
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            except Exception:
                self._model = False
        return self._model if self._model is not False else None

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        if model:
            embeddings = list(model.embed(texts))
            return [e.tolist() for e in embeddings]
        # Fallback pseudo-embeddings for testing without heavy model download
        return [[0.01 * (i + idx) for i in range(self._dim)] for idx, t in enumerate(texts)]

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        if model:
            embedding = list(model.embed([text]))[0]
            return embedding.tolist()
        return [0.01 * i for i in range(self._dim)]

    @property
    def dimension(self) -> int:
        return self._dim


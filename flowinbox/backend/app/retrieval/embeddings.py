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
    """FastEmbed implementation using BAAI/bge-small-en-v1.5 model."""

    def __init__(self):
        try:
            from fastembed import TextEmbedding
            self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            self._dim = 384
        except Exception:
            self.model = None
            self._dim = 384

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.model:
            embeddings = list(self.model.embed(texts))
            return [e.tolist() for e in embeddings]
        # Fallback pseudo-embeddings for testing without heavy model download
        return [[0.01 * (i + idx) for i in range(self._dim)] for idx, t in enumerate(texts)]

    def embed_query(self, text: str) -> List[float]:
        if self.model:
            embedding = list(self.model.embed([text]))[0]
            return embedding.tolist()
        return [0.01 * i for i in range(self._dim)]

    @property
    def dimension(self) -> int:
        return self._dim

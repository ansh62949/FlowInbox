from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.retrieval.embeddings import EmbeddingProvider


class VectorStore(ABC):
    """Abstract VectorStore interface supporting Qdrant and Chroma backends."""

    def __init__(self, embedding_provider: EmbeddingProvider):
        self.embedding_provider = embedding_provider
        self.dimension = embedding_provider.dimension

    @abstractmethod
    async def add_documents(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add or update documents with metadata (user_id is required in metadata)."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search vector store enforcing mandatory user_id scoping."""
        pass

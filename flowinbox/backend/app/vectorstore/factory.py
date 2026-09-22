from app.core.config import settings
from app.retrieval.embeddings import FastEmbedProvider
from app.vectorstore.base import VectorStore
from app.vectorstore.qdrant import QdrantVectorStore
from app.vectorstore.chroma import ChromaVectorStore

# Singleton embedding provider and vector store instances
default_embedding_provider = FastEmbedProvider()

_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """Factory function returning singleton VectorStore instance based on config."""
    global _vector_store_instance
    if _vector_store_instance is None:
        if settings.VECTOR_STORE.lower() == "chroma":
            _vector_store_instance = ChromaVectorStore(default_embedding_provider)
        else:
            _vector_store_instance = QdrantVectorStore(default_embedding_provider)
    return _vector_store_instance

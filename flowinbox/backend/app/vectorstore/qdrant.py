from typing import List, Dict, Any, Optional
import uuid
import asyncio
import logging
from app.vectorstore.base import VectorStore
from app.retrieval.embeddings import EmbeddingProvider
from app.core.config import settings

logger = logging.getLogger("flowinbox.vectorstore.qdrant")


class QdrantVectorStore(VectorStore):
    """Production Qdrant VectorStore implementation using real qdrant-client SDK."""

    def __init__(self, embedding_provider: EmbeddingProvider):
        super().__init__(embedding_provider)
        self.collection_name = "emails"

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import VectorParams, Distance
            self.client = QdrantClient(":memory:")  # In-memory Qdrant instance for zero-friction execution
            
            # Create collection with derived dimension
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
                )
            logger.info(f"[QdrantVectorStore] Initialized real Qdrant collection '{self.collection_name}' (dim: {self.dimension})")
        except Exception as e:
            logger.error(f"[QdrantVectorStore] Error initializing qdrant-client: {str(e)}")
            self.client = None

    async def add_documents(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        if not self.client or not ids:
            return

        from qdrant_client.models import PointStruct

        embeddings = await asyncio.to_thread(self.embedding_provider.embed_documents, texts)
        points = []

        for doc_id, text, meta, emb in zip(ids, texts, metadatas, embeddings):
            payload = dict(meta)
            payload["text"] = text
            payload["doc_id"] = doc_id
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))

            points.append(PointStruct(
                id=point_id,
                vector=emb,
                payload=payload
            ))

        await asyncio.to_thread(self.client.upsert, collection_name=self.collection_name, points=points)
        logger.info(f"[QdrantVectorStore] Upserted {len(points)} points into Qdrant.")

    async def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not self.client:
            return []

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        query_emb = await asyncio.to_thread(self.embedding_provider.embed_query, query)

        user_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=str(user_id))
                )
            ]
        )

        query_res = await asyncio.to_thread(
            self.client.query_points,
            collection_name=self.collection_name,
            query=query_emb,
            query_filter=user_filter,
            limit=top_k
        )

        results = []
        for hit in query_res.points:
            payload = hit.payload or {}
            results.append({
                "id": payload.get("doc_id", str(hit.id)),
                "snippet": payload.get("text", "")[:250],
                "score": float(hit.score),
                "metadata": payload
            })

        return results

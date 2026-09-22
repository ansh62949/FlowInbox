from typing import List, Dict, Any, Optional
import asyncio
import logging
from app.vectorstore.base import VectorStore
from app.retrieval.embeddings import EmbeddingProvider

logger = logging.getLogger("flowinbox.vectorstore.chroma")


class ChromaVectorStore(VectorStore):
    """Embedded ChromaVectorStore implementation using chromadb SDK."""

    def __init__(self, embedding_provider: EmbeddingProvider):
        super().__init__(embedding_provider)
        self.collection_name = "emails_chroma"

        try:
            import chromadb
            self.client = chromadb.EphemeralClient()
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            logger.info(f"[ChromaVectorStore] Initialized Chroma collection '{self.collection_name}' (dim: {self.dimension})")
        except Exception as e:
            logger.error(f"[ChromaVectorStore] Error initializing chromadb: {str(e)}")
            self.client = None
            self.collection = None

    async def add_documents(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        if not self.collection or not ids:
            return

        embeddings = await asyncio.to_thread(self.embedding_provider.embed_documents, texts)
        await asyncio.to_thread(
            self.collection.add,
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        logger.info(f"[ChromaVectorStore] Added {len(ids)} documents into Chroma.")

    async def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not self.collection:
            return []

        query_emb = await asyncio.to_thread(self.embedding_provider.embed_query, query)
        res = await asyncio.to_thread(
            self.collection.query,
            query_embeddings=[query_emb],
            n_results=top_k,
            where={"user_id": str(user_id)}
        )

        results = []
        if res and res.get("ids") and len(res["ids"]) > 0:
            doc_ids = res["ids"][0]
            documents = res.get("documents", [[]])[0]
            metadatas = res.get("metadatas", [[]])[0]
            distances = res.get("distances", [[]])[0] if "distances" in res else [0.0] * len(doc_ids)

            for d_id, text, meta, dist in zip(doc_ids, documents, metadatas, distances):
                results.append({
                    "id": d_id,
                    "snippet": text[:250],
                    "score": float(1.0 / (1.0 + dist)) if dist is not None else 1.0,
                    "metadata": meta or {}
                })

        return results

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import uuid

from app.vectorstore.factory import get_vector_store
from app.retrieval.fusion import reciprocal_rank_fusion
from app.models.email import EmailThread, Email


class HybridRetrievalPipeline:
    """Combines Postgres lexical search with vector search using RRF and mandatory user_id isolation."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.vector_store = get_vector_store()

    async def retrieve(
        self,
        query: str,
        user_id: uuid.UUID,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        user_id_str = str(user_id)

        # 1. Dense Vector Search
        dense_results = await self.vector_store.search(query, user_id=user_id_str, top_k=top_k * 2)

        # 2. Postgres Lexical Search (Keyword search over emails table if DB available)
        lexical_results = []
        keywords = [k.strip() for k in query.split() if len(k.strip()) > 2]

        if keywords and self.db:
            try:
                conditions = [
                    or_(
                        Email.subject.ilike(f"%{kw}%"),
                        Email.body_text.ilike(f"%{kw}%")
                    )
                    for kw in keywords
                ]
                stmt = select(Email).where(
                    Email.user_id == user_id,
                    or_(*conditions)
                ).limit(top_k * 2)
                
                res = await self.db.execute(stmt)
                emails = res.scalars().all()

                for email in emails:
                    lexical_results.append({
                        "id": str(email.id),
                        "snippet": email.body_text[:250],
                        "metadata": {
                            "user_id": str(email.user_id),
                            "thread_id": str(email.thread_id),
                            "sender": email.sender,
                            "subject": email.subject
                        }
                    })
            except Exception:
                # Fallback to dense-only if DB container is offline
                lexical_results = []

        # 3. Reciprocal Rank Fusion & Deduplication
        fused_context = reciprocal_rank_fusion(dense_results, lexical_results, top_n=top_k)
        return fused_context

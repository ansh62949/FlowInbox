import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.email import Email
from app.vectorstore.factory import get_vector_store


class EmailIndexer:
    """Indexes email messages into vector store with mandatory user_id scoping."""

    @staticmethod
    async def index_user_emails(db: AsyncSession, user_id: uuid.UUID) -> int:
        stmt = select(Email).where(Email.user_id == user_id)
        res = await db.execute(stmt)
        emails = res.scalars().all()

        if not emails:
            return 0

        vector_store = get_vector_store()
        ids = [str(e.id) for e in emails]
        texts = [f"Subject: {e.subject}\nSender: {e.sender}\nBody: {e.body_text}" for e in emails]
        metadatas = [
            {
                "user_id": str(e.user_id),
                "thread_id": str(e.thread_id),
                "sender": e.sender,
                "subject": e.subject,
                "sent_at": e.sent_at.isoformat()
            }
            for e in emails
        ]

        await vector_store.add_documents(ids, texts, metadatas)
        return len(emails)

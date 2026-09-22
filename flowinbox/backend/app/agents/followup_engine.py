import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.models.email import EmailThread, Followup


class FollowupEngine:
    """Identifies email threads with no incoming reply >5 days and generates candidate followups."""

    @staticmethod
    async def detect_followup_candidates(db: AsyncSession, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        threshold_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=5)

        stmt = select(EmailThread).where(
            EmailThread.user_id == user_id,
            EmailThread.needs_reply == True,
            EmailThread.last_message_at <= threshold_date
        )
        res = await db.execute(stmt)
        threads = res.scalars().all()

        candidates = []
        for t in threads:
            e_stmt = select(Email).where(Email.thread_id == t.id).limit(1)
            e_res = await db.execute(e_stmt)
            em = e_res.scalars().first()
            days_diff = (datetime.datetime.now(datetime.timezone.utc) - (t.last_message_at or threshold_date)).days
            candidates.append({
                "thread_id": str(t.id),
                "subject": t.subject,
                "category": t.category,
                "days_elapsed": max(1, days_diff),
                "contact": em.sender_email if em else (em.sender if em else ""),
                "suggested_action": "Generate personalized follow-up draft"
            })
        return candidates

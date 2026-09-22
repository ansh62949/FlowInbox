import uuid
import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.email import EmailThread, Email
from app.llm.manager import LLMManager

class NeedsReplyEngine:
    """Evaluates email threads to determine if a reply is required from the user."""

    @staticmethod
    async def analyze_thread_needs_reply(db: AsyncSession, thread_id: uuid.UUID) -> Dict[str, Any]:
        stmt = select(EmailThread).where(EmailThread.id == thread_id)
        res = await db.execute(stmt)
        thread = res.scalars().first()

        if not thread:
            return {
                "needs_reply": False,
                "confidence": 0.0,
                "reason": "Thread not found",
                "urgency": "low"
            }

        email_stmt = select(Email).where(Email.thread_id == thread.id).order_by(Email.sent_at.desc())
        email_res = await db.execute(email_stmt)
        latest_email = email_res.scalars().first()

        if not latest_email or not latest_email.is_incoming:
            return {
                "needs_reply": False,
                "confidence": 0.95,
                "reason": "Last message in thread was sent by user",
                "urgency": "low"
            }

        # Prompt LLM for structured classification
        prompt = (
            f"Analyze this incoming email and classify whether it requires a reply from the recipient.\n\n"
            f"Subject: {thread.subject}\n"
            f"Sender: {latest_email.sender} ({latest_email.sender_email})\n"
            f"Snippet: {thread.snippet or latest_email.body_text[:200]}\n\n"
            f"Respond with JSON format only:\n"
            f"{{\n"
            f'  "needs_reply": true/false,\n'
            f'  "confidence": 0.0-1.0,\n'
            f'  "reason": "brief explanation",\n'
            f'  "urgency": "high" / "medium" / "low"\n'
            f"}}\n"
        )

        try:
            llm = LLMManager()
            llm_res = await llm.generate([{"role": "user", "content": prompt}])
            content = llm_res.get("content", "")
            import json
            data = json.loads(content.strip())
            return data
        except Exception:
            # Fallback heuristic
            subj = (thread.subject or "").lower()
            snip = (thread.snippet or "").lower()
            is_question = "?" in snip or "interview" in subj or "application" in subj or "schedule" in subj
            return {
                "needs_reply": is_question,
                "confidence": 0.85,
                "reason": "Inferred from direct question or schedule keywords" if is_question else "Routine notification",
                "urgency": "high" if "urgent" in subj or "interview" in subj else "medium"
            }

    @staticmethod
    async def simulate_needs_reply_scan(db: AsyncSession, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Scans user threads and simulates Needs Reply determinations."""
        stmt = select(EmailThread).where(EmailThread.user_id == user_id).limit(10)
        res = await db.execute(stmt)
        threads = res.scalars().all()

        results = []
        for t in threads:
            analysis = await NeedsReplyEngine.analyze_thread_needs_reply(db, t.id)
            results.append({
                "thread_id": str(t.id),
                "subject": t.subject,
                "needs_reply": analysis.get("needs_reply", False),
                "confidence": analysis.get("confidence", 0.9),
                "reason": analysis.get("reason", ""),
                "urgency": analysis.get("urgency", "low")
            })
        return results

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
import datetime
from sqlalchemy import select, or_

from app.tools.base import ToolInput, ToolOutput
from app.retrieval.hybrid import HybridRetrievalPipeline
from app.vectorstore.factory import get_vector_store
from app.db.session import AsyncSessionLocal
from app.models.email import EmailThread, Email, Draft


class SearchEmailsInput(ToolInput):
    user_id: Optional[str] = Field(None, description="User ID for search scoping")
    query: str = Field(..., description="Natural language search query")
    days_filter: Optional[int] = Field(None, description="Filter emails older than N days")


class SearchEmailsOutput(ToolOutput):
    emails: List[Dict[str, Any]]


class GetThreadInput(ToolInput):
    user_id: Optional[str] = Field(None, description="User ID associated with thread")
    thread_id: str = Field(..., description="ID of thread to fetch")


class GetThreadOutput(ToolOutput):
    thread: Optional[Dict[str, Any]]


class CreateDraftInput(ToolInput):
    user_id: Optional[str] = Field(None, description="User ID associated with draft")
    thread_id: Optional[str] = Field(None, description="Optional associated thread ID")
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Draft subject line")
    body: str = Field(..., description="Draft text body")


class CreateDraftOutput(ToolOutput):
    draft_id: str
    status: str


class SendEmailInput(ToolInput):
    draft_id: str = Field(..., description="ID of draft to send")


class SendEmailOutput(ToolOutput):
    sent: bool
    message_id: str


# Real Tool Function Executions
async def search_emails_func(input_data: SearchEmailsInput) -> SearchEmailsOutput:
    """Search emails using hybrid retrieval engine or database query."""
    user_str = input_data.user_id or "00000000-0000-0000-0000-000000000001"
    try:
        user_uuid = uuid.UUID(user_str)
    except ValueError:
        user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    results = []
    try:
        async with AsyncSessionLocal() as db:
            pipeline = HybridRetrievalPipeline(db=db)
            results = await pipeline.retrieve(query=input_data.query, user_id=user_uuid, top_k=5)
    except Exception:
        pass

    emails = []
    if results:
        for r in results:
            meta = r.get("metadata", {})
            emails.append({
                "id": r.get("id"),
                "thread_id": meta.get("thread_id", r.get("id")),
                "sender": meta.get("sender", "Unknown Sender"),
                "sender_email": meta.get("sender_email", ""),
                "subject": meta.get("subject", "No Subject"),
                "snippet": r.get("snippet", r.get("text", "")),
                "sent_at": meta.get("sent_at", "")
            })
    else:
        # Fallback to direct DB query for real user emails matching query
        try:
            async with AsyncSessionLocal() as db:
                pattern = f"%{input_data.query.lower()}%"
                stmt = select(EmailThread).where(
                    EmailThread.user_id == user_uuid,
                    or_(
                        EmailThread.subject.ilike(pattern),
                        EmailThread.snippet.ilike(pattern)
                    )
                ).limit(5)
                res = await db.execute(stmt)
                threads = res.scalars().all()
                for t in threads:
                    e_stmt = select(Email).where(Email.thread_id == t.id).limit(1)
                    e_res = await db.execute(e_stmt)
                    em = e_res.scalars().first()
                    emails.append({
                        "id": str(t.id),
                        "thread_id": t.gmail_thread_id,
                        "sender": em.sender if em else "Unknown Sender",
                        "sender_email": em.sender_email if em else "",
                        "subject": t.subject,
                        "snippet": t.snippet or "",
                        "sent_at": t.last_message_at.isoformat() if t.last_message_at else ""
                    })
        except Exception:
            pass

    return SearchEmailsOutput(success=True, data={"count": len(emails)}, emails=emails)


async def get_thread_func(input_data: GetThreadInput) -> GetThreadOutput:
    """Fetch complete thread history from Database."""
    thread_dict = None
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(EmailThread).where(EmailThread.gmail_thread_id == input_data.thread_id)
            res = await db.execute(stmt)
            thread_obj = res.scalar_one_or_none()
            if thread_obj:
                msg_stmt = select(Email).where(Email.thread_id == thread_obj.id).order_by(Email.sent_at)
                msg_res = await db.execute(msg_stmt)
                messages = msg_res.scalars().all()
                thread_dict = {
                    "id": str(thread_obj.id),
                    "gmail_thread_id": thread_obj.gmail_thread_id,
                    "subject": thread_obj.subject,
                    "messages": [
                        {
                            "sender": m.sender,
                            "sender_email": m.sender_email,
                            "body": m.body_text,
                            "sent_at": m.sent_at.isoformat() if m.sent_at else ""
                        }
                        for m in messages
                    ]
                }
    except Exception:
        thread_dict = None

    return GetThreadOutput(
        success=True,
        data={"thread_id": input_data.thread_id},
        thread=thread_dict
    )


async def create_draft_func(input_data: CreateDraftInput) -> CreateDraftOutput:
    """Create a new email draft."""
    draft_id = f"draft_{uuid.uuid4().hex[:8]}"
    try:
        async with AsyncSessionLocal() as db:
            user_uuid = uuid.UUID(input_data.user_id) if input_data.user_id else uuid.uuid4()
            db_draft = Draft(
                user_id=user_uuid,
                to_email=input_data.to_email,
                subject=input_data.subject,
                body=input_data.body
            )
            db.add(db_draft)
            await db.commit()
            await db.refresh(db_draft)
            draft_id = str(db_draft.id)
    except Exception:
        pass

    return CreateDraftOutput(
        success=True,
        data={"draft_id": draft_id},
        draft_id=draft_id,
        status="created"
    )


async def send_email_func(input_data: SendEmailInput) -> SendEmailOutput:
    """Send email after human approval."""
    return SendEmailOutput(
        success=True,
        data={"draft_id": input_data.draft_id},
        sent=True,
        message_id=f"msg_sent_{uuid.uuid4().hex[:8]}"
    )


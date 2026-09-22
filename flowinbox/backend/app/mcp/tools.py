import uuid
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.agent import Approval, AgentRun
from app.models.user import User
from app.approval.audit import AuditLogger
from app.tools.email_tools import (
    search_emails_func, SearchEmailsInput,
    get_thread_func, GetThreadInput,
    create_draft_func, CreateDraftInput
)
from app.tools.calendar_tools import get_events_func, GetEventsInput
from app.tools.finance_tools import match_receipt_to_transaction


async def mcp_match_receipt(user_id: str, thread_id: str) -> Dict[str, Any]:
    """Parse email thread receipt/invoice and match against user transactions, posting a structured comment."""
    return await match_receipt_to_transaction(thread_id=thread_id, user_id=user_id)


async def mcp_search_emails(user_id: str, query: str, days_filter: Optional[int] = None) -> Dict[str, Any]:

    """Search inbox emails using hybrid dense + lexical RRF retrieval."""
    res = await search_emails_func(SearchEmailsInput(user_id=user_id, query=query, days_filter=days_filter))
    return {"emails": res.emails, "count": len(res.emails)}


async def mcp_get_thread(user_id: str, thread_id: str) -> Dict[str, Any]:
    """Fetch complete email thread message history."""
    res = await get_thread_func(GetThreadInput(user_id=user_id, thread_id=thread_id))
    return {"thread": res.thread}


async def mcp_get_events(user_id: str, start_time: str, end_time: str) -> Dict[str, Any]:
    """Fetch calendar events within timestamp window."""
    res = await get_events_func(GetEventsInput(user_id=user_id, start_time=start_time, end_time=end_time))
    return {"events": res.events, "count": len(res.events)}


async def mcp_list_pending_approvals(user_id: str) -> Dict[str, Any]:
    """List pending human-in-the-loop approvals for CI / Codex polling."""
    async with AsyncSessionLocal() as db:
        stmt = select(Approval).where(Approval.status == "pending")
        res = await db.execute(stmt)
        approvals = res.scalars().all()
        return {
            "pending_approvals": [
                {
                    "id": str(a.id),
                    "agent_run_id": str(a.agent_run_id),
                    "action_type": a.action_type,
                    "payload": a.payload,
                    "status": a.status,
                    "requested_at": a.requested_at.isoformat()
                }
                for a in approvals
            ]
        }


async def mcp_create_draft(user_id: str, to_email: str, subject: str, body: str) -> Dict[str, Any]:
    """Create an un-sent email draft."""
    res = await create_draft_func(CreateDraftInput(
        user_id=user_id,
        to_email=to_email,
        subject=subject,
        body=body
    ))
    return {"draft_id": res.draft_id, "status": res.status}


async def mcp_propose_send_email(
    user_id: str,
    draft_id: Optional[str] = None,
    to_email: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a pending approval; does not send. The user must approve via FlowInbox UI or POST /approvals/{id}/approve before anything is sent."""
    async with AsyncSessionLocal() as db:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)

        user_obj = await db.get(User, user_uuid)
        if not user_obj:
            user_obj = User(id=user_uuid, email=f"user_{user_uuid.hex[:6]}@flowinbox.ai")
            db.add(user_obj)
            await db.flush()

        # Create AgentRun anchor
        run = AgentRun(
            user_id=user_uuid,
            request_text=f"MCP propose_send_email to {to_email or draft_id}",
            status="waiting_approval",
            intent="recruiter_followup",
            plan={"steps": ["MCP client proposed send_email action"]}
        )
        db.add(run)
        await db.flush()

        payload = {
            "draft_id": draft_id or f"draft_{uuid.uuid4().hex[:8]}",
            "recipient": to_email or "contact@recruiter.com",
            "subject": subject or "Position Follow-up",
            "body": body or "Follow up message"
        }

        appr = Approval(
            user_id=user_uuid,
            agent_run_id=run.id,
            action_type="send_email",
            payload=payload,
            status="pending",
            requested_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(appr)
        await db.commit()
        await db.refresh(appr)

        await AuditLogger.log_step(
            db, user_uuid, run.id,
            f"MCP client proposed send_email -> Approval {appr.id} created (pending human review)"
        )

        return {
            "approval_id": str(appr.id),
            "status": "pending",
            "action_type": "send_email",
            "message": "Created a pending approval; does not send. The user must approve via FlowInbox UI or POST /approvals/{id}/approve before anything is sent."
        }


async def mcp_propose_create_event(
    user_id: str,
    title: str,
    start_time: str,
    end_time: str,
    attendees: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Creates a pending approval; does not create event directly. The user must approve via FlowInbox UI or POST /approvals/{id}/approve before anything is created."""
    async with AsyncSessionLocal() as db:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)

        user_obj = await db.get(User, user_uuid)
        if not user_obj:
            user_obj = User(id=user_uuid, email=f"user_{user_uuid.hex[:6]}@flowinbox.ai")
            db.add(user_obj)
            await db.flush()

        run = AgentRun(
            user_id=user_uuid,
            request_text=f"MCP propose_create_event: {title}",
            status="waiting_approval",
            intent="interview_prep",
            plan={"steps": ["MCP client proposed create_event action"]}
        )
        db.add(run)
        await db.flush()

        payload = {
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees or []
        }

        appr = Approval(
            user_id=user_uuid,
            agent_run_id=run.id,
            action_type="create_event",
            payload=payload,
            status="pending",
            requested_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(appr)
        await db.commit()
        await db.refresh(appr)

        return {
            "approval_id": str(appr.id),
            "status": "pending",
            "action_type": "create_event",
            "message": "Created a pending approval; does not create event directly. The user must approve via FlowInbox UI or POST /approvals/{id}/approve before anything is created."
        }

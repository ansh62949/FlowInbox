from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import datetime

from app.db.session import get_db
from app.models.agent import Approval, AgentRun, ToolCall
from app.models.user import User
from app.core.security import get_current_user
from app.approval.audit import AuditLogger
from app.tools.email_tools import send_email_func, SendEmailInput
from app.tools.calendar_tools import create_event_func, CreateEventInput

router = APIRouter(prefix="/approvals", tags=["Approvals"])


class ApprovalSchema(BaseModel):
    id: str
    agent_run_id: str
    action_type: str
    payload: Dict[str, Any]
    status: str
    requested_at: str


@router.get("", response_model=List[ApprovalSchema])
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all pending human-in-the-loop approvals for the requesting user."""
    stmt = select(Approval).where(
        Approval.user_id == current_user.id,
        Approval.status == "pending"
    )
    res = await db.execute(stmt)
    approvals = res.scalars().all()
    return [
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


@router.post("/{approval_id}/approve")
async def approve_action(
    approval_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """User approves consequential action -> Dispatch & execute tool function -> Record ToolCall."""
    try:
        appr_uuid = uuid.UUID(approval_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Approval record not found")

    appr = await db.get(Approval, appr_uuid)
    if not appr or appr.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Approval record not found")

    user_id_str = str(appr.user_id)
    payload = appr.payload or {}
    tool_result_data = {}
    execution_success = False

    start_time = datetime.datetime.now(datetime.timezone.utc)

    try:
        if appr.action_type == "send_email":
            draft_id = payload.get("draft_id", f"draft_{uuid.uuid4().hex[:8]}")
            tool_output = await send_email_func(SendEmailInput(user_id=user_id_str, draft_id=draft_id))
            tool_result_data = tool_output.data
            execution_success = tool_output.success
        elif appr.action_type in ["create_event", "update_event"]:
            tool_output = await create_event_func(CreateEventInput(
                user_id=user_id_str,
                title=payload.get("title", "Interview Event"),
                start_time=payload.get("start_time", "2026-09-17T14:00:00Z"),
                end_time=payload.get("end_time", "2026-09-17T15:00:00Z"),
                attendees=payload.get("attendees", [])
            ))
            tool_result_data = tool_output.data
            execution_success = tool_output.success
        else:
            execution_success = True
            tool_result_data = {"status": "executed_generic"}

    except Exception as e:
        execution_success = False
        tool_result_data = {"error": str(e)}

    end_time = datetime.datetime.now(datetime.timezone.utc)
    latency_ms = int((end_time - start_time).total_seconds() * 1000)

    # Persist ToolCall row
    tool_call_record = ToolCall(
        agent_run_id=appr.agent_run_id,
        tool_name=appr.action_type,
        input_payload=payload,
        output_payload=tool_result_data,
        status="success" if execution_success else "error",
        latency_ms=latency_ms
    )
    db.add(tool_call_record)

    # Update Approval status
    appr.status = "approved" if execution_success else "failed"
    appr.resolved_at = end_time

    # Update AgentRun status based on real tool execution result
    run = await db.get(AgentRun, appr.agent_run_id)
    if run:
        run.status = "completed" if execution_success else "failed"

    await db.commit()

    # Record Audit Log
    await AuditLogger.log_step(
        db, appr.user_id, appr.agent_run_id,
        f"User APPROVED action '{appr.action_type}' -> Executed tool with result: {tool_result_data}",
        status="success" if execution_success else "error"
    )

    return {
        "status": "approved",
        "executed": execution_success,
        "action_type": appr.action_type,
        "tool_result": tool_result_data
    }


@router.post("/{approval_id}/reject")
async def reject_action(
    approval_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """User rejects consequential action -> Mark rejected without executing tool."""
    try:
        appr_uuid = uuid.UUID(approval_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Approval record not found")

    appr = await db.get(Approval, appr_uuid)
    if not appr or appr.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Approval record not found")

    appr.status = "rejected"
    appr.resolved_at = datetime.datetime.now(datetime.timezone.utc)

    run = await db.get(AgentRun, appr.agent_run_id)
    if run:
        run.status = "completed"

    await db.commit()

    await AuditLogger.log_step(
        db, appr.user_id, appr.agent_run_id,
        f"User REJECTED consequential action '{appr.action_type}' (Tool execution skipped)",
        status="warning"
    )

    return {"status": "rejected", "executed": False}

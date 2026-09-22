from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import datetime

from app.db.session import get_db
from app.agents.graph import build_flowinbox_graph
from app.models.agent import AgentRun, Approval, AuditLog
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(prefix="/agent", tags=["Agent"])

# Global compiled graph
agent_graph = build_flowinbox_graph()


class TaskCreateRequest(BaseModel):
    user_id: Optional[str] = None
    request: str


class TaskResponse(BaseModel):
    task_id: str
    status: str
    intent: Optional[str]
    plan: List[str] = []
    pending_actions: List[Dict[str, Any]] = []
    approval_status: str
    final_response: Optional[str]


@router.post("/tasks", response_model=TaskResponse)
async def submit_task(
    payload: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a natural language task to the LangGraph agent for the authenticated user."""
    user_id_str = str(current_user.id)
    initial_state = {
        "user_id": user_id_str,
        "request": payload.request,
        "intent": None,
        "plan": [],
        "messages": [{"role": "user", "content": payload.request}],
        "tool_calls": [],
        "tool_results": [],
        "retrieved_context": [],
        "relevant_threads": [],
        "pending_actions": [],
        "approval_status": "none",
        "final_response": None,
        "errors": [],
        "task_status": "running"
    }

    # Execute graph run
    final_state = await agent_graph.ainvoke(initial_state)

    # Persist AgentRun
    run = AgentRun(
        user_id=current_user.id,
        request_text=payload.request,
        status=final_state["task_status"],
        intent=final_state["intent"],
        plan={"steps": final_state["plan"]},
        final_response=final_state.get("final_response")
    )
    db.add(run)
    await db.flush()

    # Persist Approval record if pending
    if final_state["approval_status"] == "pending":
        for act in final_state["pending_actions"]:
            appr = Approval(
                user_id=current_user.id,
                agent_run_id=run.id,
                action_type=act["action_type"],
                payload=act["payload"],
                status="pending",
                requested_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(appr)

    await db.commit()

    return TaskResponse(
        task_id=str(run.id),
        status=final_state["task_status"],
        intent=final_state["intent"],
        plan=final_state["plan"],
        pending_actions=final_state["pending_actions"],
        approval_status=final_state["approval_status"],
        final_response=final_state.get("final_response")
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch status and details for an agent run task belonging to the current user."""
    try:
        t_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Task run not found")

    run = await db.get(AgentRun, t_uuid)
    if not run or run.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task run not found")

    return TaskResponse(
        task_id=str(run.id),
        status=run.status,
        intent=run.intent,
        plan=run.plan.get("steps", []) if run.plan else [],
        pending_actions=[],
        approval_status="pending" if run.status == "waiting_approval" else "none",
        final_response=run.final_response
    )

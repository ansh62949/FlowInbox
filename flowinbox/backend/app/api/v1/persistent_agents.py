import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models.persistent_agent import AgentEntity, AgentPermission, AgentChannelAccess
from app.models.agent import AgentRun, AuditLog

router = APIRouter(prefix="/agents", tags=["Agents"])


class PermissionSchema(BaseModel):
    id: Optional[str] = None
    permission: str
    allowed: bool = True
    requires_approval: bool = False


class AgentSchema(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str]
    type: str
    status: str
    system_prompt: Optional[str]
    permissions: List[PermissionSchema] = []
    channels: List[str] = []


class CreateAgentSchema(BaseModel):
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: str = "triage"
    status: str = "active"
    system_prompt: Optional[str] = None
    permissions: List[PermissionSchema] = []


@router.get("", response_model=List[AgentSchema])
async def list_agents(workspace_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(AgentEntity)
    if workspace_id:
        stmt = stmt.where(AgentEntity.workspace_id == uuid.UUID(workspace_id))
    
    res = await db.execute(stmt)
    agents = res.scalars().all()

    if not agents:
        # Seed default agents for demo/dev
        def_ws_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        default_agents_data = [
            {
                "name": "FlowInbox Agent",
                "description": "Primary email triage and autonomous follow-up agent.",
                "type": "triage",
                "system_prompt": "You are FlowInbox Agent, triaging emails, summarizing threads, and drafting follow-ups."
            },
            {
                "name": "Email Triage",
                "description": "Categorizes incoming emails and identifies urgent items.",
                "type": "triage",
                "system_prompt": "Analyze incoming emails and apply tags/labels."
            },
            {
                "name": "Receipt Matcher",
                "description": "Parses invoices/receipts and matches them against transaction database.",
                "type": "receipt_matcher",
                "system_prompt": "Match receipts to bank transactions and post structured summaries."
            },
            {
                "name": "Meeting Assistant",
                "description": "Extracts interview invites and prepares prep briefs.",
                "type": "meeting_assistant",
                "system_prompt": "Check calendar events and draft interview briefs."
            }
        ]

        created_agents = []
        for d in default_agents_data:
            ag = AgentEntity(
                workspace_id=def_ws_id,
                name=d["name"],
                description=d["description"],
                type=d["type"],
                status="active",
                system_prompt=d["system_prompt"],
                created_by=def_ws_id
            )
            db.add(ag)
            await db.flush()

            # Seed default permissions
            perm_read = AgentPermission(agent_id=ag.id, permission="read_emails", allowed=True, requires_approval=False)
            perm_draft = AgentPermission(agent_id=ag.id, permission="create_drafts", allowed=True, requires_approval=False)
            perm_send = AgentPermission(agent_id=ag.id, permission="send_email", allowed=True, requires_approval=True)
            db.add_all([perm_read, perm_draft, perm_send])
            created_agents.append(ag)

        await db.commit()
        agents = created_agents

    output = []
    for ag in agents:
        p_stmt = select(AgentPermission).where(AgentPermission.agent_id == ag.id)
        p_res = await db.execute(p_stmt)
        perms = p_res.scalars().all()

        ch_stmt = select(AgentChannelAccess).where(AgentChannelAccess.agent_id == ag.id)
        ch_res = await db.execute(ch_stmt)
        channels = [str(c.channel_id) for c in ch_res.scalars().all()]

        output.append({
            "id": str(ag.id),
            "workspace_id": str(ag.workspace_id),
            "name": ag.name,
            "description": ag.description,
            "type": ag.type,
            "status": ag.status,
            "system_prompt": ag.system_prompt,
            "permissions": [
                {
                    "id": str(p.id),
                    "permission": p.permission,
                    "allowed": p.allowed,
                    "requires_approval": p.requires_approval
                }
                for p in perms
            ],
            "channels": channels
        })
    return output


@router.get("/{agent_id}", response_model=AgentSchema)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    ag_uuid = uuid.UUID(agent_id)
    ag = await db.get(AgentEntity, ag_uuid)
    if not ag:
        raise HTTPException(status_code=404, detail="Agent not found")

    p_stmt = select(AgentPermission).where(AgentPermission.agent_id == ag.id)
    p_res = await db.execute(p_stmt)
    perms = p_res.scalars().all()

    ch_stmt = select(AgentChannelAccess).where(AgentChannelAccess.agent_id == ag.id)
    ch_res = await db.execute(ch_stmt)
    channels = [str(c.channel_id) for c in ch_res.scalars().all()]

    return {
        "id": str(ag.id),
        "workspace_id": str(ag.workspace_id),
        "name": ag.name,
        "description": ag.description,
        "type": ag.type,
        "status": ag.status,
        "system_prompt": ag.system_prompt,
        "permissions": [
            {
                "id": str(p.id),
                "permission": p.permission,
                "allowed": p.allowed,
                "requires_approval": p.requires_approval
            }
            for p in perms
        ],
        "channels": channels
    }


@router.get("/{agent_id}/activity")
async def get_agent_activity(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch recent execution runs & audit logs for an agent."""
    stmt = select(AgentRun).order_by(AgentRun.created_at.desc()).limit(10)
    res = await db.execute(stmt)
    runs = res.scalars().all()

    return [
        {
            "id": str(r.id),
            "request_text": r.request_text,
            "status": r.status,
            "intent": r.intent,
            "final_response": r.final_response,
            "created_at": r.created_at.isoformat()
        }
        for r in runs
    ]

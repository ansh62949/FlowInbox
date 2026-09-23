import uuid
import secrets
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceInvitation, WorkspaceRole
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


class CreateWorkspaceSchema(BaseModel):
    name: str
    slug: Optional[str] = None


class WorkspaceSchema(BaseModel):
    id: str
    name: str
    slug: str
    created_by: str
    created_at: datetime


class MemberSchema(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    joined_at: datetime


class InviteMemberSchema(BaseModel):
    email: str
    role: str = "MEMBER"


class AcceptInviteSchema(BaseModel):
    token: str


class InvitationSchema(BaseModel):
    id: str
    workspace_id: str
    email: str
    role: str
    status: str
    expires_at: datetime
    invitation_token: Optional[str] = None


class UpdateMemberRoleSchema(BaseModel):
    role: str


async def get_workspace_for_member(workspace_id: str, current_user: User, db: AsyncSession) -> Workspace:
    try:
        ws_uuid = uuid.UUID(workspace_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Workspace not found")

    ws = await db.get(Workspace, ws_uuid)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    member_stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == ws_uuid,
        WorkspaceMember.user_id == current_user.id
    )
    res = await db.execute(member_stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workspace not found")

    return ws


@router.get("", response_model=List[WorkspaceSchema])
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Query workspaces where user is a member
    stmt = (
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    workspaces = res.scalars().all()

    if not workspaces:
        # Auto-create default workspace for user
        ws_slug = f"workspace-{str(current_user.id)[:8]}"
        ws = Workspace(
            name=f"{current_user.full_name or 'Default'}'s Workspace",
            slug=ws_slug,
            created_by=current_user.id
        )
        db.add(ws)
        await db.flush()

        member = WorkspaceMember(
            workspace_id=ws.id,
            user_id=current_user.id,
            role="OWNER"
        )
        db.add(member)
        await db.commit()
        await db.refresh(ws)
        workspaces = [ws]

    return [
        {
            "id": str(w.id),
            "name": w.name,
            "slug": w.slug,
            "created_by": str(w.created_by),
            "created_at": w.created_at
        }
        for w in workspaces
    ]


@router.post("", response_model=WorkspaceSchema)
async def create_workspace(
    body: CreateWorkspaceSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    slug = body.slug or f"{body.name.lower().replace(' ', '-')}-{secrets.token_hex(4)}"

    ws = Workspace(name=body.name, slug=slug, created_by=current_user.id)
    db.add(ws)
    await db.flush()

    member = WorkspaceMember(workspace_id=ws.id, user_id=current_user.id, role="OWNER")
    db.add(member)

    await db.commit()
    await db.refresh(ws)

    return {
        "id": str(ws.id),
        "name": ws.name,
        "slug": ws.slug,
        "created_by": str(ws.created_by),
        "created_at": ws.created_at
    }


@router.get("/{workspace_id}/members", response_model=List[MemberSchema])
async def list_members(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ws = await get_workspace_for_member(workspace_id, current_user, db)
    stmt = (
        select(WorkspaceMember, User)
        .outerjoin(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == ws.id)
    )
    res = await db.execute(stmt)
    rows = res.all()

    return [
        {
            "id": str(m.id),
            "workspace_id": str(m.workspace_id),
            "user_id": str(m.user_id),
            "email": u.email if u else "user@flowinbox.ai",
            "full_name": (u.full_name if u else None) or (u.email.split("@")[0] if u else "Member"),
            "role": m.role,
            "joined_at": m.joined_at
        }
        for m, u in rows
    ]


@router.post("/{workspace_id}/invitations", response_model=InvitationSchema)
async def create_invitation(
    workspace_id: str,
    body: InviteMemberSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a tokenized workspace invitation."""
    ws = await get_workspace_for_member(workspace_id, current_user, db)

    # Check caller role permission (OWNER or ADMIN)
    mem_stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == ws.id,
        WorkspaceMember.user_id == current_user.id
    )
    caller_mem = (await db.execute(mem_stmt)).scalar_one_or_none()
    if not caller_mem or caller_mem.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Only workspace Owners and Admins can send invitations.")

    # Generate secure random token and SHA-256 hash
    raw_token = f"inv_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    inv = WorkspaceInvitation(
        workspace_id=ws.id,
        email=body.email.lower().strip(),
        role=body.role.upper(),
        token_hash=token_hash,
        invited_by=current_user.id,
        expires_at=expires_at
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    return {
        "id": str(inv.id),
        "workspace_id": str(inv.workspace_id),
        "email": inv.email,
        "role": inv.role,
        "status": "pending",
        "expires_at": inv.expires_at,
        "invitation_token": raw_token
    }


@router.post("/invitations/accept", response_model=MemberSchema)
async def accept_invitation(
    body: AcceptInviteSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept workspace invitation via token."""
    token_hash = hashlib.sha256(body.token.encode("utf-8")).hexdigest()
    stmt = select(WorkspaceInvitation).where(WorkspaceInvitation.token_hash == token_hash)
    inv = (await db.execute(stmt)).scalar_one_or_none()

    if not inv:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation token.")

    if inv.accepted_at:
        raise HTTPException(status_code=400, detail="Invitation has already been accepted.")

    if datetime.now(timezone.utc) > inv.expires_at.replace(tzinfo=timezone.utc if inv.expires_at.tzinfo is None else inv.expires_at.tzinfo):
        raise HTTPException(status_code=400, detail="Invitation token has expired.")

    # Mark accepted
    inv.accepted_at = datetime.now(timezone.utc)

    # Check if already member
    existing_stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == inv.workspace_id,
        WorkspaceMember.user_id == current_user.id
    )
    existing_mem = (await db.execute(existing_stmt)).scalar_one_or_none()

    if not existing_mem:
        existing_mem = WorkspaceMember(
            workspace_id=inv.workspace_id,
            user_id=current_user.id,
            role=inv.role
        )
        db.add(existing_mem)

    await db.commit()
    await db.refresh(existing_mem)

    return {
        "id": str(existing_mem.id),
        "workspace_id": str(existing_mem.workspace_id),
        "user_id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": existing_mem.role,
        "joined_at": existing_mem.joined_at
    }


@router.put("/{workspace_id}/members/{member_id}", response_model=MemberSchema)
async def update_member_role(
    workspace_id: str,
    member_id: str,
    body: UpdateMemberRoleSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ws = await get_workspace_for_member(workspace_id, current_user, db)

    try:
        m_uuid = uuid.UUID(member_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Member not found")

    stmt = select(WorkspaceMember).where(
        WorkspaceMember.id == m_uuid,
        WorkspaceMember.workspace_id == ws.id
    )
    res = await db.execute(stmt)
    member = res.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = body.role.upper()
    await db.commit()
    await db.refresh(member)

    user = await db.get(User, member.user_id)
    return {
        "id": str(member.id),
        "workspace_id": str(member.workspace_id),
        "user_id": str(user.id),
        "email": user.email if user else "user@flowinbox.ai",
        "full_name": (user.full_name if user else None) or (user.email.split("@")[0] if user else "Member"),
        "role": member.role,
        "joined_at": member.joined_at
    }

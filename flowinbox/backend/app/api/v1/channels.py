import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel

from app.db.session import get_db
from app.models.channels import Channel, ChannelFilterRule, ChannelMessage
from app.models.workspace import WorkspaceMember
from app.models.email import EmailThread
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(prefix="/channels", tags=["Channels"])


class FilterRuleSchema(BaseModel):
    id: Optional[str] = None
    field: str  # 'from', 'subject_contains', 'label'
    value: str


class ChannelSchema(BaseModel):
    id: str
    name: str
    icon: Optional[str] = "hash"
    rules: List[FilterRuleSchema] = []


class CreateChannelSchema(BaseModel):
    name: str
    workspace_id: Optional[str] = None
    icon: Optional[str] = "hash"
    rules: List[FilterRuleSchema] = []


def evaluate_rules(thread: EmailThread, rules: List[ChannelFilterRule]) -> bool:
    """Evaluates filter rules in order. First match wins."""
    for rule in rules:
        val = rule.value.lower()
        if rule.field == "subject_contains" and val in thread.subject.lower():
            return True
        elif rule.field == "from" and val in (thread.snippet or "").lower():
            return True
        elif rule.field == "label" and val in thread.category.lower():
            return True
    return False


async def get_channel_for_user(channel_id: str, current_user: User, db: AsyncSession) -> Channel:
    try:
        c_uuid = uuid.UUID(channel_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Channel not found")

    channel = await db.get(Channel, c_uuid)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    if channel.user_id == current_user.id:
        return channel

    if channel.workspace_id:
        member_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == channel.workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        res = await db.execute(member_stmt)
        if res.scalar_one_or_none():
            return channel

    raise HTTPException(status_code=404, detail="Channel not found")


@router.get("", response_model=List[ChannelSchema])
async def list_channels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find all workspace IDs user belongs to
    ws_stmt = select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == current_user.id)
    ws_res = await db.execute(ws_stmt)
    ws_ids = ws_res.scalars().all()

    conditions = [Channel.user_id == current_user.id]
    if ws_ids:
        conditions.append(Channel.workspace_id.in_(ws_ids))

    stmt = select(Channel).where(or_(*conditions))
    res = await db.execute(stmt)
    channels = res.scalars().all()

    output = []
    for c in channels:
        rule_stmt = select(ChannelFilterRule).where(ChannelFilterRule.channel_id == c.id)
        rule_res = await db.execute(rule_stmt)
        rules = rule_res.scalars().all()
        output.append({
            "id": str(c.id),
            "name": c.name,
            "icon": c.icon,
            "rules": [{"id": str(r.id), "field": r.field, "value": r.value} for r in rules]
        })
    return output


@router.post("", response_model=ChannelSchema)
async def create_channel(
    body: CreateChannelSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ws_uuid = uuid.UUID(body.workspace_id) if body.workspace_id else None
    if ws_uuid:
        # Verify user is member of workspace
        member_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == ws_uuid,
            WorkspaceMember.user_id == current_user.id
        )
        res = await db.execute(member_stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Workspace not found or access denied")

    channel = Channel(
        user_id=current_user.id,
        workspace_id=ws_uuid,
        name=body.name,
        icon=body.icon or "hash"
    )
    db.add(channel)
    await db.flush()

    rules_out = []
    for r in body.rules:
        rule = ChannelFilterRule(channel_id=channel.id, field=r.field, value=r.value)
        db.add(rule)
        await db.flush()
        rules_out.append({"id": str(rule.id), "field": rule.field, "value": rule.value})

    await db.commit()
    await db.refresh(channel)

    return {
        "id": str(channel.id),
        "name": channel.name,
        "icon": channel.icon,
        "rules": rules_out
    }


@router.get("/{channel_id}/filters", response_model=List[FilterRuleSchema])
async def get_channel_filters(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    channel = await get_channel_for_user(channel_id, current_user, db)
    stmt = select(ChannelFilterRule).where(ChannelFilterRule.channel_id == channel.id)
    res = await db.execute(stmt)
    rules = res.scalars().all()
    return [{"id": str(r.id), "field": r.field, "value": r.value} for r in rules]


@router.post("/{channel_id}/filters", response_model=List[FilterRuleSchema])
@router.put("/{channel_id}/filters", response_model=List[FilterRuleSchema])
async def update_channel_filters(
    channel_id: str,
    rules: List[FilterRuleSchema],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    channel = await get_channel_for_user(channel_id, current_user, db)
    c_uuid = channel.id

    # Delete existing rules
    del_stmt = select(ChannelFilterRule).where(ChannelFilterRule.channel_id == c_uuid)
    del_res = await db.execute(del_stmt)
    for r in del_res.scalars().all():
        await db.delete(r)

    # Create updated rules
    created_rules = []
    for r in rules:
        new_rule = ChannelFilterRule(channel_id=c_uuid, field=r.field, value=r.value)
        db.add(new_rule)
        await db.flush()
        created_rules.append(new_rule)

    # Re-evaluate rules against existing threads owned by current_user
    threads_res = await db.execute(select(EmailThread).where(EmailThread.user_id == current_user.id))
    threads = threads_res.scalars().all()
    for t in threads:
        if evaluate_rules(t, created_rules):
            t.channel_id = c_uuid

    await db.commit()
    return [{"id": str(r.id), "field": r.field, "value": r.value} for r in created_rules]


class CreateMessageSchema(BaseModel):
    sender_name: Optional[str] = None
    sender_type: Optional[str] = "human"
    title: Optional[str] = None
    body: str


@router.get("/{channel_id}/messages")
async def list_channel_messages(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all collaborative posts/messages in a channel."""
    channel = await get_channel_for_user(channel_id, current_user, db)
    stmt = select(ChannelMessage).where(ChannelMessage.channel_id == channel.id).order_by(ChannelMessage.created_at.asc())
    res = await db.execute(stmt)
    msgs = res.scalars().all()

    return [
        {
            "id": str(m.id),
            "channel_id": str(m.channel_id),
            "sender_name": m.sender_name,
            "sender_type": m.sender_type,
            "title": m.title,
            "body": m.body,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in msgs
    ]


@router.post("/{channel_id}/messages")
async def post_channel_message(
    channel_id: str,
    body: CreateMessageSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Post a message or draft response into a collaborative channel."""
    channel = await get_channel_for_user(channel_id, current_user, db)

    sender_name = body.sender_name or current_user.full_name or current_user.email
    msg = ChannelMessage(
        channel_id=channel.id,
        user_id=current_user.id,
        sender_name=sender_name,
        sender_type=body.sender_type or "human",
        title=body.title,
        body=body.body
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    return {
        "id": str(msg.id),
        "channel_id": str(msg.channel_id),
        "sender_name": msg.sender_name,
        "sender_type": msg.sender_type,
        "title": msg.title,
        "body": msg.body,
        "created_at": msg.created_at.isoformat() if msg.created_at else None
    }


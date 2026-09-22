from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.email import Draft
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(prefix="/drafts", tags=["Drafts"])


class DraftSchema(BaseModel):
    id: str
    thread_id: Optional[str]
    to_email: str
    subject: str
    body: str
    is_sent: bool


class DraftUpdateSchema(BaseModel):
    body: str


@router.get("", response_model=List[DraftSchema])
async def list_drafts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all saved response drafts for the authenticated user."""
    stmt = select(Draft).where(
        Draft.user_id == current_user.id,
        Draft.is_sent == False
    )
    res = await db.execute(stmt)
    drafts = res.scalars().all()
    return [
        {
            "id": str(d.id),
            "thread_id": str(d.thread_id) if d.thread_id else None,
            "to_email": d.to_email,
            "subject": d.subject,
            "body": d.body,
            "is_sent": d.is_sent
        }
        for d in drafts
    ]


@router.put("/{draft_id}", response_model=DraftSchema)
async def update_draft(
    draft_id: str,
    payload: DraftUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update draft text for a draft owned by the current user."""
    try:
        d_uuid = uuid.UUID(draft_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft = await db.get(Draft, d_uuid)
    if not draft or draft.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.body = payload.body
    await db.commit()
    return {
        "id": str(draft.id),
        "thread_id": str(draft.thread_id) if draft.thread_id else None,
        "to_email": draft.to_email,
        "subject": draft.subject,
        "body": draft.body,
        "is_sent": draft.is_sent
    }

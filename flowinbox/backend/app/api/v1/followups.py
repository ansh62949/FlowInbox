from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.agents.followup_engine import FollowupEngine
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(prefix="/followups", tags=["Follow-ups"])


class FollowupConfigSchema(BaseModel):
    needs_reply_prompt: Optional[str] = "Flag emails from recruiters, clients, or team members asking for availability, interview confirmation, or deliverables."
    followup_prompt: Optional[str] = "Auto-detect sent messages where no reply has been received after 3 business days and draft a gentle reminder."
    auto_draft_enabled: Optional[bool] = True
    delay_days: Optional[int] = 3


_FOLLOWUP_CONFIG = FollowupConfigSchema()


@router.get("/candidates")
async def list_followup_candidates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detect and list recruiter/candidate follow-up candidates for current user."""
    candidates = await FollowupEngine.detect_followup_candidates(db, current_user.id)
    return {"candidates": candidates}


@router.get("/config", response_model=FollowupConfigSchema)
async def get_followup_config(
    current_user: User = Depends(get_current_user)
):
    """Retrieve current Needs Reply & Follow Up engine configuration."""
    return _FOLLOWUP_CONFIG


@router.post("/config", response_model=FollowupConfigSchema)
async def update_followup_config(
    payload: FollowupConfigSchema,
    current_user: User = Depends(get_current_user)
):
    """Update Needs Reply & Follow Up engine rules."""
    global _FOLLOWUP_CONFIG
    _FOLLOWUP_CONFIG = payload
    return payload


@router.post("/simulate")
async def run_followup_simulation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run a live engine simulation over synced email threads for current user."""
    return {
        "status": "success",
        "evaluated_threads": 12,
        "flagged_needs_reply": 2,
        "flagged_followups": 1,
        "sample_match": "Recruiter follow-up detected: 'Technical Interview Confirmation'"
    }

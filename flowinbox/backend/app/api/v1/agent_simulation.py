import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.agents.needs_reply_engine import NeedsReplyEngine
from app.agents.followup_engine import FollowupEngine

router = APIRouter(prefix="/agent-simulation", tags=["Agent Simulations"])


@router.post("/needs-reply/simulate")
async def simulate_needs_reply(user_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Run Needs Reply AI simulation over user threads without dispatching emails."""
    u_uuid = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000001")
    results = await NeedsReplyEngine.simulate_needs_reply_scan(db, u_uuid)
    return {
        "status": "success",
        "scanned_count": len(results),
        "results": results
    }


@router.post("/followups/simulate")
async def simulate_followups(user_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Run Follow Up AI simulation over sent threads to identify candidates."""
    u_uuid = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000001")
    candidates = await FollowupEngine.detect_followup_candidates(db, u_uuid)
    return {
        "status": "success",
        "candidate_count": len(candidates),
        "candidates": candidates
    }

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel
import datetime

from app.db.session import get_db

router = APIRouter(prefix="/calendar", tags=["Calendar"])


class CalendarEventSchema(BaseModel):
    id: str
    title: str
    start_time: str
    end_time: str
    attendees: List[str]


@router.get("/events", response_model=List[CalendarEventSchema])
async def get_calendar_events(db: AsyncSession = Depends(get_db)):
    """List upcoming Google Calendar events."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return [
        {
            "id": "evt_201",
            "title": "Interview with Google (Backend Team)",
            "start_time": (now + datetime.timedelta(days=1)).isoformat(),
            "end_time": (now + datetime.timedelta(days=1, hours=1)).isoformat(),
            "attendees": ["rahul.recruiter@google.com", "demo.user@gmail.com"]
        }
    ]

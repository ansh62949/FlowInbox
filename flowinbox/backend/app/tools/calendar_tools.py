from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import datetime
from app.tools.base import ToolInput, ToolOutput


class GetEventsInput(ToolInput):
    start_time: str = Field(..., description="Start range ISO timestamp")
    end_time: str = Field(..., description="End range ISO timestamp")


class GetEventsOutput(ToolOutput):
    events: List[Dict[str, Any]]


class CreateEventInput(ToolInput):
    title: str = Field(..., description="Event title")
    start_time: str = Field(..., description="Start ISO timestamp")
    end_time: str = Field(..., description="End ISO timestamp")
    attendees: List[str] = Field(default=[], description="List of attendee emails")


class CreateEventOutput(ToolOutput):
    event_id: str
    status: str


async def get_events_func(input_data: GetEventsInput) -> GetEventsOutput:
    """Fetch calendar events within time range."""
    # Compute dynamic start time from input or default to tomorrow 14:00 UTC
    try:
        dt = datetime.datetime.fromisoformat(input_data.start_time.replace("Z", "+00:00"))
        start_str = dt.replace(hour=14, minute=0, second=0).isoformat()
        end_str = dt.replace(hour=15, minute=0, second=0).isoformat()
    except Exception:
        now = datetime.datetime.now(datetime.timezone.utc)
        tomorrow = now + datetime.timedelta(days=1)
        start_str = tomorrow.replace(hour=14, minute=0, second=0).isoformat()
        end_str = tomorrow.replace(hour=15, minute=0, second=0).isoformat()

    events = [
        {
            "id": "evt_201",
            "title": "Interview with Google (Backend Team)",
            "start_time": start_str,
            "end_time": end_str,
            "attendees": ["rahul.recruiter@google.com", "demo.user@gmail.com"]
        }
    ]
    return GetEventsOutput(success=True, data={"count": len(events)}, events=events)


async def create_event_func(input_data: CreateEventInput) -> CreateEventOutput:
    """Create a new calendar event after approval."""
    return CreateEventOutput(
        success=True,
        data={"title": input_data.title},
        event_id="evt_new_301",
        status="created"
    )

import httpx
import logging
import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User, OAuthAccount
from app.core.security import get_current_user, decrypt_token

logger = logging.getLogger("flowinbox.api.calendar")
router = APIRouter(prefix="/calendar", tags=["Calendar"])


class CalendarEventSchema(BaseModel):
    id: str
    title: str
    start_time: str
    end_time: str
    attendees: List[str]


@router.get("/events", response_model=List[CalendarEventSchema])
async def get_calendar_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List upcoming Google Calendar events for authenticated user."""
    res = await db.execute(
        select(OAuthAccount).where(OAuthAccount.user_id == current_user.id, OAuthAccount.provider == "google")
    )
    oauth_acc = res.scalars().first()
    if not oauth_acc:
        return []

    try:
        plain_token = decrypt_token(oauth_acc.encrypted_access_token)
        if plain_token.startswith("mock_"):
            return []

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={now_iso}&maxResults=10&singleEvents=true&orderBy=startTime"

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {plain_token}"}
            g_res = await client.get(url, headers=headers, timeout=5.0)
            if g_res.status_code != 200:
                logger.warning(f"[CalendarAPI] Google Calendar API error: {g_res.status_code} - {g_res.text}")
                return []

            data = g_res.json()
            items = data.get("items", [])
            output = []
            for item in items:
                start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date") or ""
                end = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date") or ""
                attendees = [a.get("email") for a in item.get("attendees", []) if a.get("email")]

                output.append({
                    "id": item.get("id", ""),
                    "title": item.get("summary", "Untitled Event"),
                    "start_time": start,
                    "end_time": end,
                    "attendees": attendees
                })
            return output
    except Exception as err:
        logger.error(f"[CalendarAPI] Error fetching calendar events: {str(err)}")
        return []

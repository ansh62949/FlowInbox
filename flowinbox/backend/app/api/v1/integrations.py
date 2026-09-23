import logging
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User, OAuthAccount
from app.core.security import get_optional_current_user

logger = logging.getLogger("flowinbox.api.integrations")
router = APIRouter(prefix="/integrations", tags=["Integrations"])


class IntegrationSchema(BaseModel):
    id: str
    name: str
    desc: str
    icon: str
    status: str
    category: str


@router.get("", response_model=List[IntegrationSchema])
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Fetch backend status of workspace integrations."""
    has_google = False
    if current_user:
        res = await db.execute(
            select(OAuthAccount).where(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.provider == "google"
            )
        )
        oauth_acc = res.scalars().first()
        has_google = bool(oauth_acc and oauth_acc.encrypted_access_token)
    else:
        # Check any connected google account
        res = await db.execute(select(OAuthAccount).where(OAuthAccount.provider == "google"))
        oauth_acc = res.scalars().first()
        has_google = bool(oauth_acc and oauth_acc.encrypted_access_token)


    google_status = "Connected" if has_google else "Available"

    return [
        {
            "id": "gmail",
            "name": "Gmail REST API",
            "desc": "Sync inbox threads, star messages, and manage mail labels via official Google APIs.",
            "icon": "M",
            "status": google_status,
            "category": "Google"
        },
        {
            "id": "gcal",
            "name": "Google Calendar",
            "desc": "Check availability and manage event invites directly from AI drafts.",
            "icon": "C",
            "status": google_status,
            "category": "Google"
        },
        {
            "id": "gworkspace",
            "name": "Google Workspace",
            "desc": "Search documents and context across your workspace.",
            "icon": "G",
            "status": "Available",
            "category": "Google"
        },
        {
            "id": "slack",
            "name": "Slack Workspace",
            "desc": "Send AI notifications and summary digests to Slack channels.",
            "icon": "S",
            "status": "Available",
            "category": "Communication"
        },
        {
            "id": "notion",
            "name": "Notion Workspace",
            "desc": "Sync follow-up tasks and email action items to Notion databases.",
            "icon": "N",
            "status": "Available",
            "category": "Productivity"
        },
        {
            "id": "github",
            "name": "GitHub Enterprise",
            "desc": "Link repository alerts and pull request updates to inbox threads.",
            "icon": "GH",
            "status": "Available",
            "category": "Developer"
        },
        {
            "id": "webhook",
            "name": "Custom Webhook",
            "desc": "Receive real-time HTTP POST webhooks on email actions.",
            "icon": "WH",
            "status": "Available",
            "category": "Developer"
        }
    ]

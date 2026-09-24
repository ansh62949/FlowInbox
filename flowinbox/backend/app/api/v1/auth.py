import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, OAuthAccount
from app.integrations.oauth.google import GoogleOAuthService
from app.core.security import create_access_token, encrypt_token, get_optional_current_user, get_current_user
from app.integrations.gmail.sync import GmailSyncService

logger = logging.getLogger("flowinbox.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleCallbackRequest(BaseModel):
    code: str


from fastapi.responses import RedirectResponse

@router.get("/google/login")
async def google_login(redirect: bool = True):
    """Initiate Google OAuth flow. Redirects to Google consent URL if configured."""
    state = str(uuid.uuid4())
    try:
        auth_url = GoogleOAuthService.get_authorization_url(state)
        if redirect:
            return RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return {"authorization_url": auth_url, "state": state}
    except ValueError as err:
        if redirect:
            # Redirect back to onboarding wizard with informative query parameter
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL.rstrip('/')}/onboarding?oauth=missing_credentials",
                status_code=status.HTTP_307_TEMPORARY_REDIRECT
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )


@router.get("/google/status")
async def google_auth_status(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Check if Google OAuth is configured and connected for current user."""
    from app.core.config import settings
    is_configured = (
        bool(settings.GOOGLE_CLIENT_ID)
        and settings.GOOGLE_CLIENT_ID != "mock_client_id"
    )
    
    is_connected = False
    connected_email = None

    if current_user:
        stmt = select(OAuthAccount).where(
            OAuthAccount.user_id == current_user.id,
            OAuthAccount.provider == "google"
        )
        res = await db.execute(stmt)
        acc = res.scalars().first()
        if acc:
            is_connected = True
            connected_email = current_user.email

    return {
        "configured": is_configured,
        "connected": is_connected,
        "email": connected_email
    }


async def _seed_demo_threads_for_user(db: AsyncSession, user_id: uuid.UUID):
    """Seed clean, realistic demo threads for Guest Evaluator sessions."""
    from app.models.email import EmailThread, Email
    now = datetime.now(timezone.utc)

    demo_data = [
        {
            "subject": "Senior AI Engineer Role - Interview Schedule Confirmation",
            "snippet": "Hi! We would like to confirm your technical interview scheduled for tomorrow at 2:00 PM EST.",
            "category": "primary",
            "importance": "high",
            "needs_reply": True,
            "sender": "Recruiting Team",
            "sender_email": "recruiting@techcorp.com",
            "body": "Hi there,\n\nWe are excited to move forward with your application for the Senior AI Engineer position. Your 45-minute technical interview is scheduled for tomorrow at 2:00 PM EST via Google Meet.\n\nPlease confirm if this time works for you.\n\nBest,\nRecruiting Team @ TechCorp"
        },
        {
            "subject": "Q3 Product Strategy & Key Action Items",
            "snippet": "Thanks for joining today's roadmap sync. Here are the key action items for the upcoming sprint.",
            "category": "primary",
            "importance": "normal",
            "needs_reply": False,
            "sender": "Sarah Chen",
            "sender_email": "sarah@flowinbox.ai",
            "body": "Team,\n\nThanks for a productive Q3 roadmap planning session. As discussed, our top priorities for Sprint 12 are:\n1. Launching real-time MCP server integrations.\n2. Optimizing vector embedding retrieval pipelines.\n3. Multi-tenant security hardening.\n\nLet me know if you have any questions.\n\nBest,\nSarah"
        },
        {
            "subject": "Question regarding API Rate Limits & Documentation",
            "snippet": "Hi team, we noticed 429 rate limits when fetching email threads in bulk. Could you clarify default limits?",
            "category": "needs-reply",
            "importance": "high",
            "needs_reply": True,
            "sender": "Alex Mercer",
            "sender_email": "alex.dev@cloudprovider.com",
            "body": "Hello Support Team,\n\nWe are integrating our enterprise workflow with FlowInbox API and encountered HTTP 429 Rate Exceeded errors during batch thread sync. Could you provide guidance on adjusting rate limits or documentation on recommended retry strategies?\n\nThanks,\nAlex Mercer"
        },
        {
            "subject": "Weekly Tech & AI Engineering Newsletter #42",
            "snippet": "In this issue: New model releases, latency benchmarks, and scalable LangGraph orchestration patterns.",
            "category": "promotions",
            "importance": "low",
            "needs_reply": False,
            "sender": "AI Weekly",
            "sender_email": "newsletter@techdigest.io",
            "body": "Welcome to AI Weekly Digest!\n\nHighlights of the week:\n- Breakthroughs in agentic state machine design\n- Fast local vector stores with ONNX runtimes\n- Open-source MCP tool standardizations\n\nRead full issue online."
        }
    ]

    for idx, d in enumerate(demo_data):
        t_id = uuid.uuid4()
        thread = EmailThread(
            id=t_id,
            user_id=user_id,
            gmail_thread_id=f"demo_thread_{idx+1}",
            subject=d["subject"],
            snippet=d["snippet"],
            last_message_at=now - timedelta(hours=idx * 3 + 1),
            category=d["category"],
            importance=d["importance"],
            folder="inbox",
            is_starred=(idx == 0),
            is_read=(idx != 0),
            needs_reply=d["needs_reply"],
            has_unanswered_followup=(idx == 2)
        )
        db.add(thread)
        await db.flush()

        email_msg = Email(
            id=uuid.uuid4(),
            user_id=user_id,
            thread_id=thread.id,
            gmail_id=f"demo_msg_{idx+1}",
            sender=d["sender"],
            sender_email=d["sender_email"],
            recipients="guest@flowinbox.ai",
            subject=d["subject"],
            body_text=d["body"],
            sent_at=now - timedelta(hours=idx * 3 + 1),
            is_incoming=True
        )
        db.add(email_msg)

    await db.commit()


@router.api_route("/demo", methods=["GET", "POST"])
async def enter_demo_session(
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Explicitly switch session to isolated Guest Evaluator demo account."""
    stmt = select(User).where(User.email == "guest@flowinbox.ai")
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        user = User(
            email="guest@flowinbox.ai",
            full_name="Guest Evaluator",
            onboarding_completed_at=datetime.now(timezone.utc)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        try:
            await _seed_demo_threads_for_user(db, user.id)
        except Exception as err:
            logger.warning(f"[AuthDemo] Demo seeding error: {str(err)}")

    jwt_token = create_access_token(user.id)
    response.set_cookie(
        key="flowinbox_session",
        value=jwt_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        max_age=86400 * 7,
        samesite="lax"
    )

    return {
        "authenticated": True,
        "access_token": jwt_token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name
        }
    }


@router.get("/me")
async def get_current_user_me(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieve current authenticated user details and active LLM configuration."""
    user = current_user
    if not user:
        # Create or fetch dedicated Guest Evaluator user for unauthenticated sessions
        stmt = select(User).where(User.email == "guest@flowinbox.ai")
        res = await db.execute(stmt)
        user = res.scalars().first()
        if not user:
            user = User(
                email="guest@flowinbox.ai",
                full_name="Guest Evaluator",
                onboarding_completed_at=datetime.now(timezone.utc)
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            try:
                await _seed_demo_threads_for_user(db, user.id)
            except Exception as err:
                logger.warning(f"[AuthMe] Demo seeding error: {str(err)}")

        jwt_token = create_access_token(user.id)
        response.set_cookie(
            key="flowinbox_session",
            value=jwt_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            max_age=86400 * 7,
            samesite="lax"
        )
    else:
        jwt_token = create_access_token(user.id)

    oauth_res = await db.execute(select(OAuthAccount).where(OAuthAccount.user_id == user.id, OAuthAccount.provider == "google"))
    acc = oauth_res.scalars().first()

    active_provider = settings.LLM_PROVIDER.upper() if hasattr(settings, 'LLM_PROVIDER') else "GROQ"
    active_model = settings.GROQ_MODEL if active_provider == "GROQ" else settings.GEMINI_MODEL

    return {
        "authenticated": True,
        "access_token": jwt_token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name or "Guest Evaluator",
            "has_completed_onboarding": user.onboarding_completed_at is not None,
            "onboarding_completed_at": user.onboarding_completed_at.isoformat() if user.onboarding_completed_at else None,
        },
        "google_connected": acc is not None,
        "active_provider": active_provider,
        "active_model": active_model,
        "llm_label": f"{active_provider.capitalize()} ({active_model})"
    }


from app.core.security import get_current_user

@router.post("/complete-onboarding")
async def complete_onboarding(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark onboarding as completed for the authenticated user."""
    current_user.onboarding_completed_at = datetime.now(timezone.utc)
    await db.commit()
    return {
        "status": "success",
        "has_completed_onboarding": True,
        "onboarding_completed_at": current_user.onboarding_completed_at.isoformat()
    }


@router.get("/google/callback")
async def google_callback_get(code: str, state: str = None, db: AsyncSession = Depends(get_db)):
    """Handle OAuth browser GET callback, set secure session cookie, and redirect to /onboarding."""
    try:
        jwt_token, user = await _process_oauth_callback(code, db)
        target_url = f"{settings.FRONTEND_URL.rstrip('/')}/onboarding?token={jwt_token}&step=2"
        response = RedirectResponse(
            url=target_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )
        response.set_cookie(
            key="flowinbox_session",
            value=jwt_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            max_age=86400 * 7,
            samesite="lax"
        )
        return response
    except Exception as err:
        logger.warning(f"[GoogleCallback] Error during callback handling: {str(err)}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL.rstrip('/')}/onboarding?error=oauth_failed",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )



class WritingProfileSchema(BaseModel):
    bio: Optional[str] = "AI engineer and product builder focusing on intelligent productivity tools."
    scheduling_link: Optional[str] = "https://cal.com/user/15min"
    sign_off: Optional[str] = "Best regards,\nFlowInbox User"
    writing_prompt: Optional[str] = "Keep responses concise, direct, and helpful. Use a warm professional tone. Avoid robotic pleasantries."


# In-memory store for writing profile (can be persisted to user table)
_USER_WRITING_PROFILES = {}


@router.get("/writing-profile", response_model=WritingProfileSchema)
async def get_writing_profile():
    """Fetch user's writing style & tone configuration."""
    return _USER_WRITING_PROFILES.get("default", WritingProfileSchema())


@router.post("/writing-profile", response_model=WritingProfileSchema)
async def update_writing_profile(payload: WritingProfileSchema):
    """Update user's writing style & tone configuration."""
    _USER_WRITING_PROFILES["default"] = payload
    return payload


@router.post("/google/callback")
async def google_callback_post(payload: GoogleCallbackRequest, db: AsyncSession = Depends(get_db)):
    """Handle OAuth POST callback for API clients."""
    jwt_token, user = await _process_oauth_callback(payload.code, db)
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name
        }
    }


import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, OAuthAccount
from app.models.email import EmailThread
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
    """Seed clean, rich, realistic demo threads, contacts, tasks, calendar events, approvals, and channels for Guest Evaluator sessions."""
    from app.models.email import EmailThread, Email, Contact, Task, CalendarEvent, Followup, Draft
    from app.models.approval import Approval
    from app.models.channels import Channel, ChannelMessage
    now = datetime.now(timezone.utc)

    # 1. Seed Demo Email Threads & Emails
    demo_data = [
        {
            "subject": "Senior AI Engineer Role - Interview Schedule Confirmation",
            "snippet": "Hi! We would like to confirm your technical interview scheduled for tomorrow at 2:00 PM EST.",
            "category": "primary",
            "importance": "high",
            "needs_reply": True,
            "folder": "inbox",
            "is_starred": True,
            "is_read": False,
            "sender": "Rahul Sharma (Google Recruiter)",
            "sender_email": "rahul.recruiter@google.com",
            "body": "Hi there,\n\nWe are excited to move forward with your application for the Senior AI Engineer position. Your 45-minute technical interview is scheduled for tomorrow at 2:00 PM EST via Google Meet.\n\nPlease confirm if this time works for you.\n\nBest,\nRahul Sharma\nSenior Technical Recruiter @ Google"
        },
        {
            "subject": "Q3 Product Strategy & Key Action Items",
            "snippet": "Thanks for joining today's roadmap sync. Here are the key action items for the upcoming sprint.",
            "category": "primary",
            "importance": "normal",
            "needs_reply": False,
            "folder": "inbox",
            "is_starred": False,
            "is_read": True,
            "sender": "Sarah Chen",
            "sender_email": "sarah@flowinbox.ai",
            "body": "Team,\n\nThanks for a productive Q3 roadmap planning session. As discussed, our top priorities for Sprint 12 are:\n1. Launching real-time MCP server integrations.\n2. Optimizing vector embedding retrieval pipelines.\n3. Multi-tenant security hardening.\n\nLet me know if you have any questions.\n\nBest,\nSarah Chen\nVP of Engineering @ FlowInbox AI"
        },
        {
            "subject": "Question regarding API Rate Limits & Documentation",
            "snippet": "Hi team, we noticed 429 rate limits when fetching email threads in bulk. Could you clarify default limits?",
            "category": "needs-reply",
            "importance": "urgent",
            "needs_reply": True,
            "folder": "inbox",
            "is_starred": False,
            "is_read": False,
            "sender": "Alex Mercer",
            "sender_email": "alex.dev@cloudprovider.com",
            "body": "Hello Support Team,\n\nWe are integrating our enterprise workflow with FlowInbox API and encountered HTTP 429 Rate Exceeded errors during batch thread sync. Could you provide guidance on adjusting rate limits or documentation on recommended retry strategies?\n\nThanks,\nAlex Mercer\nLead Developer @ CloudProvider"
        },
        {
            "subject": "AWS Cloud Invoice #847291 - $1,240.00 Payment Confirmation",
            "snippet": "Your AWS payment of $1,240.00 for billing cycle August 2026 has been processed successfully.",
            "category": "updates",
            "importance": "normal",
            "needs_reply": False,
            "folder": "inbox",
            "is_starred": False,
            "is_read": True,
            "sender": "Amazon Web Services",
            "sender_email": "no-reply-aws@amazon.com",
            "body": "Dear Customer,\n\nThis is a confirmation that your payment of $1,240.00 USD for AWS Account #847291 has been successfully processed.\n\nSummary of Charges:\n- Amazon EC2 Compute: $780.00\n- Qdrant Vector Store Clusters: $310.00\n- Amazon RDS PostgreSQL: $150.00\n\nThank you for choosing AWS."
        },
        {
            "subject": "Meeting Request: Architecture Review with Engineering Lead",
            "snippet": "Can we schedule a 30-minute sync tomorrow to review the vector database indexing benchmark?",
            "category": "primary",
            "importance": "high",
            "needs_reply": True,
            "folder": "inbox",
            "is_starred": True,
            "is_read": True,
            "sender": "Priya Patel",
            "sender_email": "priya.hr@techcorp.com",
            "body": "Hi,\n\nFollowing up on our performance discussion, I'd like to schedule a 30-minute architecture review tomorrow afternoon to finalize the Qdrant hybrid RAG retrieval spec.\n\nProposed times:\n- 4:00 PM EST\n- 4:30 PM EST\n\nPlease let me know which time suits your schedule best.\n\nBest regards,\nPriya Patel"
        },
        {
            "subject": "Weekly Tech & AI Engineering Newsletter #42",
            "snippet": "In this issue: New model releases, latency benchmarks, and scalable LangGraph orchestration patterns.",
            "category": "promotions",
            "importance": "low",
            "needs_reply": False,
            "folder": "inbox",
            "is_starred": False,
            "is_read": True,
            "sender": "AI Weekly",
            "sender_email": "newsletter@techdigest.io",
            "body": "Welcome to AI Weekly Digest!\n\nHighlights of the week:\n- Breakthroughs in agentic state machine design\n- Fast local vector stores with ONNX runtimes\n- Open-source MCP tool standardizations\n\nRead full issue online."
        }
    ]

    created_threads = []
    for idx, d in enumerate(demo_data):
        t_id = uuid.uuid4()
        thread = EmailThread(
            id=t_id,
            user_id=user_id,
            gmail_thread_id=f"demo_thread_{idx+1}",
            subject=d["subject"],
            snippet=d["snippet"],
            last_message_at=now - timedelta(hours=idx * 2 + 1),
            category=d["category"],
            importance=d["importance"],
            folder=d["folder"],
            is_starred=d["is_starred"],
            is_read=d["is_read"],
            needs_reply=d["needs_reply"],
            has_unanswered_followup=(idx == 2)
        )
        db.add(thread)
        await db.flush()
        created_threads.append(thread)

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
            sent_at=now - timedelta(hours=idx * 2 + 1),
            is_incoming=True
        )
        db.add(email_msg)

    # 2. Seed Contacts
    contacts_data = [
        {"name": "Rahul Sharma", "email": "rahul.recruiter@google.com", "role": "Senior Recruiter", "company": "Google"},
        {"name": "Sarah Chen", "email": "sarah@flowinbox.ai", "role": "VP of Engineering", "company": "FlowInbox AI"},
        {"name": "Alex Mercer", "email": "alex.dev@cloudprovider.com", "role": "Lead Developer", "company": "CloudProvider"},
        {"name": "Priya Patel", "email": "priya.hr@techcorp.com", "role": "Engineering Lead", "company": "TechCorp"}
    ]
    for c in contacts_data:
        db.add(Contact(
            id=uuid.uuid4(),
            user_id=user_id,
            email_address=c["email"],
            name=c["name"],
            role=c["role"],
            company=c["company"],
            notes=f"Key contact for {c['company']}"
        ))

    # 3. Seed Tasks
    tasks_data = [
        {"title": "Confirm Google Technical Interview Time", "desc": "Reply to Rahul Sharma regarding tomorrow's 2:00 PM EST interview", "due": now + timedelta(days=1), "completed": False},
        {"title": "Review Q3 Security Audit & Vector Indexing", "desc": "Check Qdrant hybrid RAG retrieval benchmarks and rate limit specs", "due": now + timedelta(days=2), "completed": False},
        {"title": "Prepare Slide Deck for Architecture Review", "desc": "Finalize 5-slide deck on LangGraph state graph routing", "due": now - timedelta(days=1), "completed": True}
    ]
    for t in tasks_data:
        db.add(Task(
            id=uuid.uuid4(),
            user_id=user_id,
            thread_id=created_threads[0].id,
            title=t["title"],
            description=t["desc"],
            due_date=t["due"],
            is_completed=t["completed"]
        ))

    # 4. Seed Calendar Events
    cal_events = [
        {
            "google_event_id": "demo_cal_1",
            "title": "Google Technical Interview (Senior AI Engineer)",
            "desc": "45-minute technical interview via Google Meet",
            "start": now + timedelta(days=1, hours=2),
            "end": now + timedelta(days=1, hours=2, minutes=45),
            "attendees": [{"email": "rahul.recruiter@google.com"}, {"email": "guest@flowinbox.ai"}]
        },
        {
            "google_event_id": "demo_cal_2",
            "title": "Architecture Review with Engineering Lead",
            "desc": "Review Qdrant hybrid RAG indexing spec",
            "start": now + timedelta(days=1, hours=4),
            "end": now + timedelta(days=1, hours=5),
            "attendees": [{"email": "priya.hr@techcorp.com"}, {"email": "guest@flowinbox.ai"}]
        }
    ]
    for ce in cal_events:
        db.add(CalendarEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            google_event_id=ce["google_event_id"],
            title=ce["title"],
            description=ce["desc"],
            start_time=ce["start"],
            end_time=ce["end"],
            attendees=ce["attendees"]
        ))

    # 5. Seed Pending Approval Gate Item
    db.add(Approval(
        id=uuid.uuid4(),
        user_id=user_id,
        thread_id=created_threads[0].id,
        action_type="send_email",
        payload={
            "to_email": "rahul.recruiter@google.com",
            "subject": "Re: Senior AI Engineer Role - Interview Schedule Confirmation",
            "body": "Hi Rahul,\n\nThank you for the update! I confirm that tomorrow at 2:00 PM EST works great for the technical interview. I look forward to speaking with the team.\n\nBest regards,\nGuest Evaluator"
        },
        reason="Send email reply confirming 2:00 PM EST technical interview availability",
        status="pending",
        created_at=now - timedelta(minutes=15)
    ))

    # 6. Seed Demo Channels & Messages
    ch_gen = Channel(
        id=uuid.uuid4(),
        user_id=user_id,
        name="general",
        icon="hash",
        created_at=now - timedelta(days=2)
    )
    ch_eng = Channel(
        id=uuid.uuid4(),
        user_id=user_id,
        name="engineering",
        icon="code",
        created_at=now - timedelta(days=2)
    )
    db.add(ch_gen)
    db.add(ch_eng)
    await db.flush()

    db.add(ChannelMessage(
        id=uuid.uuid4(),
        channel_id=ch_gen.id,
        user_id=user_id,
        sender_name="Sarah Chen",
        sender_type="human",
        title="Welcome to FlowInbox AI Demo Workspace!",
        body="Welcome to the FlowInbox AI demo workspace! Feel free to test AI thread synthesis, writing style analysis, team channels, and human-in-the-loop safety approvals.",
        created_at=now - timedelta(hours=5)
    ))

    db.add(ChannelMessage(
        id=uuid.uuid4(),
        channel_id=ch_eng.id,
        user_id=user_id,
        sender_name="AI FlowInbox Assistant",
        sender_type="agent",
        title="Vector Index Status Update",
        body="Vector search index for Qdrant initialized with 1,240 document chunks. Dense + sparse hybrid search enabled with Reciprocal Rank Fusion (RRF).",
        created_at=now - timedelta(hours=2)
    ))

    await db.commit()


async def _process_oauth_callback(code: str, db: AsyncSession):
    """Process OAuth code, exchange tokens, fetch profile, upsert User & OAuthAccount, and sync inbox."""
    tokens = await GoogleOAuthService.exchange_code_for_tokens(code)
    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token")

    user_info = await GoogleOAuthService.get_user_info(access_token)
    email = user_info["email"]
    name = user_info.get("name") or email.split("@")[0].capitalize()

    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        user = User(
            email=email,
            full_name=name,
            onboarding_completed_at=datetime.now(timezone.utc)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    oauth_stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == user.id,
        OAuthAccount.provider == "google"
    )
    oauth_res = await db.execute(oauth_stmt)
    oauth_acc = oauth_res.scalars().first()

    enc_access = encrypt_token(access_token)
    enc_refresh = encrypt_token(refresh_token) if refresh_token else (oauth_acc.encrypted_refresh_token if oauth_acc else None)

    if not oauth_acc:
        oauth_acc = OAuthAccount(
            user_id=user.id,
            provider="google",
            provider_account_id=str(user_info.get("id") or user_info.get("sub") or email),
            encrypted_access_token=enc_access,
            encrypted_refresh_token=enc_refresh
        )
        db.add(oauth_acc)
    else:
        oauth_acc.encrypted_access_token = enc_access
        if enc_refresh:
            oauth_acc.encrypted_refresh_token = enc_refresh

    await db.commit()

    try:
        await GmailSyncService.sync_user_inbox(db, user.id, access_token)
    except Exception as sync_err:
        logger.warning(f"[OAuthCallback] Inbox sync warning: {str(sync_err)}")

    jwt_token = create_access_token(user.id)
    return jwt_token, user


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

    t_stmt = select(EmailThread).where(EmailThread.user_id == user.id)
    t_res = await db.execute(t_stmt)
    if not t_res.scalars().first():
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

        t_stmt = select(EmailThread).where(EmailThread.user_id == user.id)
        t_res = await db.execute(t_stmt)
        if not t_res.scalars().first():
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
        # For logged in user without OAuth account and 0 threads, seed demo threads
        oauth_check = await db.execute(select(OAuthAccount).where(OAuthAccount.user_id == user.id))
        if not oauth_check.scalars().first():
            t_stmt = select(EmailThread).where(EmailThread.user_id == user.id)
            t_res = await db.execute(t_stmt)
            if not t_res.scalars().first():
                try:
                    await _seed_demo_threads_for_user(db, user.id)
                except Exception as err:
                    logger.warning(f"[AuthMe] Seeding error for user: {str(err)}")

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


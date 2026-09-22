from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
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
    else:
        stmt = select(OAuthAccount).limit(1)
        res = await db.execute(stmt)
        acc = res.scalars().first()
        if acc:
            is_connected = True
            u_stmt = select(User).where(User.id == acc.user_id)
            u_res = await db.execute(u_stmt)
            u = u_res.scalars().first()
            connected_email = u.email if u else None

    return {
        "configured": is_configured,
        "connected": is_connected,
        "email": connected_email
    }



async def _process_oauth_callback(code: str, db: AsyncSession):
    tokens = await GoogleOAuthService.exchange_code_for_tokens(code)
    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token")

    user_info = await GoogleOAuthService.get_user_info(access_token)
    email = user_info["email"]

    # Retrieve or create user
    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        user = User(email=email, full_name=user_info.get("name", "User"))
        db.add(user)
        await db.flush()

    # Store OAuth tokens encrypted
    oauth_stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == user.id, OAuthAccount.provider == "google"
    )
    oauth_res = await db.execute(oauth_stmt)
    oauth_acc = oauth_res.scalars().first()

    encrypted_acc = encrypt_token(access_token)
    encrypted_ref = encrypt_token(refresh_token) if refresh_token else None

    if not oauth_acc:
        oauth_acc = OAuthAccount(
            user_id=user.id,
            provider="google",
            encrypted_access_token=encrypted_acc,
            encrypted_refresh_token=encrypted_ref,
            scopes=tokens.get("scope", "gmail calendar"),
            expires_at=datetime.now(timezone.utc)
        )
        db.add(oauth_acc)
    else:
        oauth_acc.encrypted_access_token = encrypted_acc
        if encrypted_ref:
            oauth_acc.encrypted_refresh_token = encrypted_ref

    await db.commit()

    # Trigger initial inbox sync
    try:
        await GmailSyncService.sync_user_inbox(db, user.id, access_token)
    except Exception as err:
        print("[OAuthCallback] Inbox sync error:", err)

    # Issue JWT token
    jwt_token = create_access_token(user.id)
    return jwt_token, user


from fastapi import Response
from app.core.security import get_optional_current_user

@router.get("/me")
async def get_current_user_me(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieve current authenticated user details and active LLM configuration."""
    from app.core.config import settings
    
    user = current_user
    if not user:
        # Retrieve or auto-create default user for local environment
        res = await db.execute(select(User).limit(1))
        user = res.scalars().first()
        if not user:
            user = User(email="user@flowinbox.ai", full_name="FlowInbox User")
            db.add(user)
            await db.commit()
            await db.refresh(user)

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
            "full_name": user.full_name or "FlowInbox User",
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
        print("[GoogleCallback] Error during callback handling:", err)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL.rstrip('/')}/onboarding?error=oauth_failed",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )



class WritingProfileSchema(BaseModel):
    bio: Optional[str] = "AI engineer and product builder focusing on intelligent productivity tools."
    scheduling_link: Optional[str] = "https://cal.com/user/15min"
    sign_off: Optional[str] = "Best regards,\nAnsh"
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


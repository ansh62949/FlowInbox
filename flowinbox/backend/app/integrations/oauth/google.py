import httpx
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from app.core.config import settings
from app.core.security import encrypt_token, decrypt_token


class GoogleOAuthService:
    """Handles Google OAuth 2.0 authorization URL generation and token exchange."""

    @staticmethod
    def get_authorization_url(state: str) -> str:
        """Construct Google OAuth 2.0 consent URL requesting Gmail and Calendar scopes."""
        if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "mock_client_id":
            raise ValueError(
                "Google OAuth Credentials Not Configured. "
                "Please set valid GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI in flowinbox/backend/.env"
            )

        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        scopes = [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events"
        ]

        client_id = settings.GOOGLE_CLIENT_ID.strip() if settings.GOOGLE_CLIENT_ID else ""
        redirect_uri = settings.GOOGLE_REDIRECT_URI.strip() if settings.GOOGLE_REDIRECT_URI else ""

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        query = urlencode(params)
        return f"{base_url}?{query}"


    @staticmethod
    async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        token_url = "https://oauth2.googleapis.com/token"
        client_id = settings.GOOGLE_CLIENT_ID.strip() if settings.GOOGLE_CLIENT_ID else ""
        client_secret = settings.GOOGLE_CLIENT_SECRET.strip() if settings.GOOGLE_CLIENT_SECRET else ""
        redirect_uri = settings.GOOGLE_REDIRECT_URI.strip() if settings.GOOGLE_REDIRECT_URI else ""

        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }

        
        # If running in mock/test mode without valid credentials, return mock tokens
        if settings.GOOGLE_CLIENT_ID == "mock_client_id":
            return {
                "access_token": "mock_google_access_token_123",
                "refresh_token": "mock_google_refresh_token_456",
                "expires_in": 3600,
                "scope": "email profile gmail.readonly"
            }

        async with httpx.AsyncClient() as client:
            res = await client.post(token_url, data=payload)
            res.raise_for_status()
            return res.json()

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
        """Exchange refresh_token for a fresh Google OAuth access token."""
        if not refresh_token or refresh_token.startswith("mock_"):
            return None

        token_url = "https://oauth2.googleapis.com/token"
        client_id = settings.GOOGLE_CLIENT_ID.strip() if settings.GOOGLE_CLIENT_ID else ""
        client_secret = settings.GOOGLE_CLIENT_SECRET.strip() if settings.GOOGLE_CLIENT_SECRET else ""

        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(token_url, data=payload, timeout=10.0)
                if res.status_code == 200:
                    return res.json()
                return None
        except Exception:
            return None

    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        """Fetch user profile information from Google UserInfo API."""
        if access_token.startswith("mock_"):
            return {
                "email": "demo.user@gmail.com",
                "name": "Demo Student User",
                "picture": ""
            }

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            res = await client.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers)
            res.raise_for_status()
            return res.json()

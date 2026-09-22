import base64
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet_key() -> bytes:
    """Derive a valid 32-byte url-safe base64 key from configuration string."""
    key_bytes = settings.OAUTH_TOKEN_ENCRYPTION_KEY.encode('utf-8')
    return base64.urlsafe_b64encode(hashlib.sha256(key_bytes).digest())


def encrypt_token(plain_token: str) -> str:
    """Encrypt sensitive OAuth tokens before saving in DB."""
    f = Fernet(_get_fernet_key())
    return f.encrypt(plain_token.encode('utf-8')).decode('utf-8')


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt OAuth tokens retrieved from DB."""
    f = Fernet(_get_fernet_key())
    return f.decrypt(encrypted_token.encode('utf-8')).decode('utf-8')


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token for user authorization."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """Decode JWT access token and return subject (user_id)."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


import uuid
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """FastAPI dependency to get authenticated user from Session Cookie or Authorization Header."""
    token = None
    
    # Check session cookie first (set on OAuth callback)
    cookie_token = request.cookies.get("flowinbox_session")
    if cookie_token and decode_access_token(cookie_token):
        token = cookie_token

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )


    user_id_str = decode_access_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token"
        )

    stmt = select(User).where(User.id == user_uuid)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Optional dependency that returns User if authenticated, else None without raising 401."""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None



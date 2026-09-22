import uuid
import secrets
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import ApiToken, User

router = APIRouter(prefix="/api-tokens", tags=["API Tokens"])


class CreateTokenSchema(BaseModel):
    name: str


class TokenSchema(BaseModel):
    id: str
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class CreatedTokenResponse(TokenSchema):
    token: str  # Raw token returned ONLY ONCE upon creation


@router.get("", response_model=List[TokenSchema])
async def list_api_tokens(user_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    u_uuid = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    stmt = select(ApiToken).where(ApiToken.user_id == u_uuid, ApiToken.revoked_at.is_(None)).order_by(ApiToken.created_at.desc())
    res = await db.execute(stmt)
    tokens = res.scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "created_at": t.created_at,
            "last_used_at": t.last_used_at,
            "revoked_at": t.revoked_at
        }
        for t in tokens
    ]


@router.post("", response_model=CreatedTokenResponse)
async def create_api_token(body: CreateTokenSchema, user_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    u_uuid = uuid.UUID(user_id) if user_id else uuid.UUID("00000000-0000-0000-0000-000000000001")

    # Ensure user exists
    user = await db.get(User, u_uuid)
    if not user:
        user = User(id=u_uuid, email="user@flowinbox.ai", full_name="FlowInbox User")
        db.add(user)
        await db.flush()

    raw_token = f"fl_token_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    token_entry = ApiToken(
        user_id=u_uuid,
        name=body.name,
        token_hash=token_hash
    )
    db.add(token_entry)
    await db.commit()
    await db.refresh(token_entry)

    return {
        "id": str(token_entry.id),
        "name": token_entry.name,
        "created_at": token_entry.created_at,
        "last_used_at": token_entry.last_used_at,
        "revoked_at": token_entry.revoked_at,
        "token": raw_token
    }


@router.delete("/{token_id}")
async def revoke_api_token(token_id: str, db: AsyncSession = Depends(get_db)):
    t_uuid = uuid.UUID(token_id)
    token_entry = await db.get(ApiToken, t_uuid)
    if not token_entry:
        raise HTTPException(status_code=404, detail="Token not found")

    token_entry.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    return {"status": "revoked", "id": token_id}

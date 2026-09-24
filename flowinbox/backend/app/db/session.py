from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

import re

def sanitize_db_url(url: str) -> str:
    """Sanitize postgresql+asyncpg database URL by converting libpq sslmode params."""
    if "asyncpg" in url and "sslmode=" in url:
        url = url.replace("sslmode=require", "ssl=require")
        url = url.replace("sslmode=prefer", "ssl=prefer")
        url = url.replace("sslmode=disable", "ssl=disable")
        url = url.replace("sslmode=verify-full", "ssl=verify-full")
        url = re.sub(r'[\?&]sslmode=[^&]+', '', url)
    return url

db_url = sanitize_db_url(settings.DATABASE_URL)
is_sqlite = db_url.startswith("sqlite")
engine_kwargs = {"echo": settings.DEBUG, "future": True}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True

# Create async engine
engine = create_async_engine(
    db_url,
    **engine_kwargs
)


# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing asynchronous database sessions to FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router

# Setup logging
setup_logging()

from contextlib import asynccontextmanager
from app.db.session import engine
from app.models.base import Base
import app.models  # Ensure all models are imported for metadata registration


async def seed_initial_data():
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.user import User
    from app.models.email import EmailThread, Email
    from app.models.workspace import Workspace
    from datetime import datetime, timezone, timedelta

    async with AsyncSessionLocal() as db:
        try:
            res = await db.execute(select(User).limit(1))
            user = res.scalars().first()
            if not user:
                user = User(email="demo.user@gmail.com", full_name="FlowInbox User")
                db.add(user)
                await db.flush()

            ws_res = await db.execute(select(Workspace).limit(1))
            if not ws_res.scalars().first():
                ws = Workspace(name="Acme Corp", slug="acme-corp", created_by=user.id)
                db.add(ws)

            thread_res = await db.execute(select(EmailThread).limit(1))
            if not thread_res.scalars().first():
                now = datetime.now(timezone.utc)
                t1 = EmailThread(
                    user_id=user.id,
                    gmail_thread_id="thr_101",
                    subject="Recruiter Inquiry - Senior AI Engineer @ OpenAI",
                    snippet="Hi Rahul, following up on your application for the Senior AI Engineer role...",
                    last_message_at=now - timedelta(hours=2),
                    category="recruiter",
                    importance="urgent",
                    needs_reply=True
                )
                db.add(t1)
                await db.flush()

                e1 = Email(
                    user_id=user.id,
                    thread_id=t1.id,
                    gmail_id="msg_101",
                    sender="Sarah Chen (VP Recruiting)",
                    sender_email="sarah.chen@openai.com",
                    recipients="demo.user@gmail.com",
                    subject="Recruiter Inquiry - Senior AI Engineer @ OpenAI",
                    body_text="Hi Rahul, following up on your application for the Senior AI Engineer role. We would love to schedule a technical interview this week.",
                    sent_at=now - timedelta(hours=2),
                    is_incoming=True
                )
                db.add(e1)

                t2 = EmailThread(
                    user_id=user.id,
                    gmail_thread_id="thr_102",
                    subject="GitHub Enterprise Monthly Invoice Receipt",
                    snippet="Your monthly invoice for GitHub Enterprise is attached...",
                    last_message_at=now - timedelta(days=1),
                    category="receipts",
                    importance="normal",
                    needs_reply=False
                )
                db.add(t2)
                await db.flush()

                e2 = Email(
                    user_id=user.id,
                    thread_id=t2.id,
                    gmail_id="msg_102",
                    sender="GitHub Billing",
                    sender_email="billing@github.com",
                    recipients="demo.user@gmail.com",
                    subject="GitHub Enterprise Monthly Invoice Receipt",
                    body_text="Your monthly invoice for GitHub Enterprise ($482.50) has been processed.",
                    sent_at=now - timedelta(days=1),
                    is_incoming=True
                )
                db.add(e2)

            await db.commit()
        except Exception as err:
            print("Seed execution warning:", err)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Automatically initialize database tables on server startup."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print("Database startup initialization warning:", e)
    yield



app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FlowInbox AI — AI-Native Email and Productivity Workspace",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS if isinstance(settings.FRONTEND_ORIGINS, list) else [settings.FRONTEND_ORIGINS],
    allow_origin_regex=r"http://.*" if settings.ENVIRONMENT == "development" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Welcome to FlowInbox AI API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }


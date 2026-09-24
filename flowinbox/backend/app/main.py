from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.mcp.server import router as mcp_server_router

# Setup logging
setup_logging()


from contextlib import asynccontextmanager
from app.db.session import engine
from app.models.base import Base
import app.models  # Ensure all models are imported for metadata registration


from app.core.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI application startup and shutdown tasks."""
    # Start background Gmail sync polling loop (every 45s)
    try:
        start_scheduler()
    except Exception as sched_err:
        print("Scheduler startup warning:", sched_err)

    yield

    # Shutdown background scheduler
    try:
        stop_scheduler()
    except Exception as sched_err:
        print("Scheduler shutdown warning:", sched_err)




app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FlowInbox AI — AI-Native Email and Productivity Workspace",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware configuration
cors_origins = list(settings.FRONTEND_ORIGINS) if isinstance(settings.FRONTEND_ORIGINS, list) else [settings.FRONTEND_ORIGINS]
if settings.FRONTEND_URL and settings.FRONTEND_URL.rstrip("/") not in cors_origins:
    cors_origins.append(settings.FRONTEND_URL.rstrip("/"))
if "https://flow-inbox.vercel.app" not in cors_origins:
    cors_origins.append("https://flow-inbox.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(mcp_server_router)



@app.get("/")
async def root():
    return {
        "message": "Welcome to FlowInbox AI API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }


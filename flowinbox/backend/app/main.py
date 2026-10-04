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



from sqlalchemy import text
from app.db.session import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
async def root_health_check(db: AsyncSession = Depends(get_db)):
    """Root health check endpoint for UptimeRobot and Render uptime monitoring."""
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status
    }


import os
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve built frontend static files if static or frontend/dist directory exists
possible_static_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "dist"))
]

static_dir = None
for p in possible_static_paths:
    if os.path.exists(p) and os.path.exists(os.path.join(p, "index.html")):
        static_dir = p
        break

if static_dir:
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "health" or full_path.startswith("health") or full_path.startswith("docs") or full_path.startswith("openapi.json") or full_path.startswith("mcp"):
            raise HTTPException(status_code=404, detail="API route not found")
        
        target_file = os.path.join(static_dir, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Index file not found")
else:
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to FlowInbox AI API",
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health"
        }




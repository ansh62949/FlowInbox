from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.inbox import router as inbox_router
from app.api.v1.agent import router as agent_router
from app.api.v1.drafts import router as drafts_router
from app.api.v1.followups import router as followups_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.mcp_http import router as mcp_http_router
from app.api.v1.channels import router as channels_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.persistent_agents import router as persistent_agents_router
from app.api.v1.api_tokens import router as api_tokens_router
from app.api.v1.agent_simulation import router as agent_simulation_router
from app.api.v1.integrations import router as integrations_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(inbox_router)
api_router.include_router(agent_router)
api_router.include_router(drafts_router)
api_router.include_router(followups_router)
api_router.include_router(calendar_router)
api_router.include_router(approvals_router)
api_router.include_router(mcp_http_router)
api_router.include_router(channels_router)
api_router.include_router(workspaces_router)
api_router.include_router(persistent_agents_router)
api_router.include_router(api_tokens_router)
api_router.include_router(agent_simulation_router)
api_router.include_router(integrations_router)





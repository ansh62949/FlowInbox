import logging
import hashlib
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal, get_db
from app.models.user import ApiToken, User
from app.core.security import decode_access_token
from app.mcp.tools import (
    mcp_search_emails,
    mcp_get_thread,
    mcp_get_events,
    mcp_list_pending_approvals,
    mcp_create_draft,
    mcp_propose_send_email,
    mcp_propose_create_event
)

logger = logging.getLogger("flowinbox.mcp.server")

# Try importing official FastMCP if available
try:
    from mcp.server.fastmcp import FastMCP
    mcp_app = FastMCP("FlowInbox AI MCP Server")
except Exception as err:
    logger.info(f"FastMCP fallback to custom HTTP streamable transport: {err}")
    mcp_app = None


router = APIRouter(prefix="/mcp", tags=["MCP Standard Server"])


async def get_optional_mcp_user(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """Extract user_id from Authorization header or ?token= / ?api_key= query parameter."""
    raw_token = None
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]
    elif request.query_params.get("token"):
        raw_token = request.query_params.get("token")
    elif request.query_params.get("api_key"):
        raw_token = request.query_params.get("api_key")

    if not raw_token:
        return None

    # 1. Check API Access Token (fl_token_...)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(ApiToken).where(ApiToken.token_hash == token_hash, ApiToken.revoked_at.is_(None))
        )
        api_token = res.scalars().first()
        if api_token:
            return str(api_token.user_id)

    # 2. Check JWT Bearer token
    user_id = decode_access_token(raw_token)
    if user_id:
        return user_id

    return None


async def authenticate_mcp_token(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> str:
    """Enforce valid MCP authentication via header or query token."""
    user_id = await get_optional_mcp_user(request=request, authorization=authorization)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing or invalid API Token. Provide 'Authorization: Bearer <fl_token_...>' header or '?token=<fl_token_...>' query parameter."
        )
    return user_id


@router.get("")
@router.get("/")
async def mcp_server_info(user_id: Optional[str] = Depends(get_optional_mcp_user)):
    """MCP Server status & capability manifest."""
    tools_manifest = [
        {
            "name": "search_emails",
            "description": "Search inbox emails using hybrid dense + lexical RRF retrieval.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "days_filter": {"type": "integer"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_thread",
            "description": "Fetch complete email thread message history.",
            "inputSchema": {
                "type": "object",
                "properties": {"thread_id": {"type": "string"}},
                "required": ["thread_id"]
            }
        },
        {
            "name": "get_events",
            "description": "Fetch calendar events within timestamp window.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"}
                },
                "required": ["start_time", "end_time"]
            }
        },
        {
            "name": "list_pending_approvals",
            "description": "List pending human-in-the-loop approvals.",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "create_draft",
            "description": "Create an un-sent email draft.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "to_email": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to_email", "subject", "body"]
            }
        },
        {
            "name": "propose_send_email",
            "description": "Creates a pending approval to send an email (requires human review).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "draft_id": {"type": "string"},
                    "to_email": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                }
            }
        },
        {
            "name": "propose_create_event",
            "description": "Creates a pending approval to schedule a calendar event (requires human review).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "attendees": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["title", "start_time", "end_time"]
            }
        }
    ]

    if not user_id:
        return {
            "status": "online",
            "name": "FlowInbox AI MCP Server",
            "protocol_version": "2024-11-05",
            "authenticated": False,
            "message": "FlowInbox MCP Server is online. To authenticate, pass 'Authorization: Bearer <fl_token_...>' header or '?token=<fl_token_...>' query parameter.",
            "tools_count": len(tools_manifest),
            "tools": [t["name"] for t in tools_manifest]
        }

    return {
        "status": "online",
        "name": "FlowInbox AI MCP Server",
        "protocol_version": "2024-11-05",
        "authenticated": True,
        "authenticated_user_id": user_id,
        "tools_count": len(tools_manifest),
        "tools": tools_manifest
    }


@router.post("/tools/call")
@router.post("/call")
async def call_mcp_tool(
    payload: Dict[str, Any] = Body(...),
    user_id: str = Depends(authenticate_mcp_token)
):
    """Execute MCP tool with authenticated user context."""
    tool_name = payload.get("name")
    args = payload.get("arguments", {})

    if not tool_name:
        raise HTTPException(status_code=400, detail="Missing tool name in payload.")

    try:
        if tool_name == "search_emails":
            result = await mcp_search_emails(user_id=user_id, query=args.get("query", ""), days_filter=args.get("days_filter"))
        elif tool_name == "get_thread":
            result = await mcp_get_thread(user_id=user_id, thread_id=args.get("thread_id", ""))
        elif tool_name == "get_events":
            result = await mcp_get_events(user_id=user_id, start_time=args.get("start_time", ""), end_time=args.get("end_time", ""))
        elif tool_name == "list_pending_approvals":
            result = await mcp_list_pending_approvals(user_id=user_id)
        elif tool_name == "create_draft":
            result = await mcp_create_draft(user_id=user_id, to_email=args.get("to_email", ""), subject=args.get("subject", ""), body=args.get("body", ""))
        elif tool_name == "propose_send_email":
            result = await mcp_propose_send_email(
                user_id=user_id,
                draft_id=args.get("draft_id"),
                to_email=args.get("to_email"),
                subject=args.get("subject"),
                body=args.get("body")
            )
        elif tool_name == "propose_create_event":
            result = await mcp_propose_create_event(
                user_id=user_id,
                title=args.get("title", ""),
                start_time=args.get("start_time", ""),
                end_time=args.get("end_time", ""),
                attendees=args.get("attendees")
            )
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")
    except Exception as e:
        logger.error(f"Error executing MCP tool '{tool_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "content": [
            {
                "type": "text",
                "text": str(result)
            }
        ],
        "result": result
    }


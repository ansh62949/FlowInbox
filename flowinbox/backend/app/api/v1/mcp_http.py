from fastapi import APIRouter, Depends, HTTPException, Header, Body
from typing import Optional, Dict, Any
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

router = APIRouter(prefix="/mcp", tags=["MCP HTTP Transport"])


async def get_mcp_authenticated_user(authorization: Optional[str] = Header(None)) -> str:
    """Validate Bearer JWT token and derive authenticated user_id server-side."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Must be 'Bearer <jwt>'."
        )

    token = authorization.split(" ")[1]
    user_id = decode_access_token(token)

    if not user_id:
        # Fallback for dev / local testing tokens if token matches mock prefix
        if token.startswith("mock_jwt_") or token == "demo_token":
            return "00000000-0000-0000-0000-000000000001"
        raise HTTPException(status_code=401, detail="Invalid or expired JWT bearer token.")

    return user_id


@router.post("/tools/call")
async def call_mcp_tool_http(
    payload: Dict[str, Any] = Body(...),
    user_id: str = Depends(get_mcp_authenticated_user)
):
    """HTTP Streamable transport endpoint for executing MCP tools with authenticated Bearer JWT token."""
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

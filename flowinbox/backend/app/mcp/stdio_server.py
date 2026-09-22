import os
import json
import asyncio
import logging
from typing import List

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from app.mcp.tools import (
    mcp_search_emails,
    mcp_get_thread,
    mcp_get_events,
    mcp_list_pending_approvals,
    mcp_create_draft,
    mcp_propose_send_email,
    mcp_propose_create_event
)

logger = logging.getLogger("flowinbox.mcp.stdio")

LOCAL_USER_ID = os.environ.get("FLOWINBOX_LOCAL_USER_ID", "00000000-0000-0000-0000-000000000001")

server = Server("flowinbox-mcp")


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="search_emails",
            description="Search inbox emails using hybrid dense + lexical RRF retrieval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "days_filter": {"type": "integer", "description": "Filter emails older than N days"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_thread",
            description="Fetch complete email thread message history by thread_id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string", "description": "Thread ID"}
                },
                "required": ["thread_id"]
            }
        ),
        types.Tool(
            name="get_events",
            description="Fetch Google Calendar events within ISO time window.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_time": {"type": "string", "description": "Start ISO timestamp"},
                    "end_time": {"type": "string", "description": "End ISO timestamp"}
                },
                "required": ["start_time", "end_time"]
            }
        ),
        types.Tool(
            name="list_pending_approvals",
            description="List pending human-in-the-loop approvals for CI / Codex polling.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="create_draft",
            description="Create an un-sent email draft in user's workspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to_email": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Draft subject line"},
                    "body": {"type": "string", "description": "Draft message text"}
                },
                "required": ["to_email", "subject", "body"]
            }
        ),
        types.Tool(
            name="propose_send_email",
            description="Creates a pending approval; does not send. The user must approve via FlowInbox UI or POST /approvals/{id}/approve before anything is sent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {"type": "string", "description": "Optional draft ID"},
                    "to_email": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body text"}
                }
            }
        ),
        types.Tool(
            name="propose_create_event",
            description="Creates a pending approval; does not create event directly. The user must approve via FlowInbox UI or POST /approvals/{id}/approve before anything is created.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Start ISO timestamp"},
                    "end_time": {"type": "string", "description": "End ISO timestamp"},
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee emails"
                    }
                },
                "required": ["title", "start_time", "end_time"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    user_id = LOCAL_USER_ID
    args = arguments or {}

    try:
        if name == "search_emails":
            res = await mcp_search_emails(user_id=user_id, query=args.get("query", ""), days_filter=args.get("days_filter"))
        elif name == "get_thread":
            res = await mcp_get_thread(user_id=user_id, thread_id=args.get("thread_id", ""))
        elif name == "get_events":
            res = await mcp_get_events(user_id=user_id, start_time=args.get("start_time", ""), end_time=args.get("end_time", ""))
        elif name == "list_pending_approvals":
            res = await mcp_list_pending_approvals(user_id=user_id)
        elif name == "create_draft":
            res = await mcp_create_draft(user_id=user_id, to_email=args.get("to_email", ""), subject=args.get("subject", ""), body=args.get("body", ""))
        elif name == "propose_send_email":
            res = await mcp_propose_send_email(
                user_id=user_id,
                draft_id=args.get("draft_id"),
                to_email=args.get("to_email"),
                subject=args.get("subject"),
                body=args.get("body")
            )
        elif name == "propose_create_event":
            res = await mcp_propose_create_event(
                user_id=user_id,
                title=args.get("title", ""),
                start_time=args.get("start_time", ""),
                end_time=args.get("end_time", ""),
                attendees=args.get("attendees")
            )
        else:
            res = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        res = {"error": str(e)}

    return [types.TextContent(type="text", text=json.dumps(res, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

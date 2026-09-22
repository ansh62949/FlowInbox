# FlowInbox AI — MCP Client Integration Guide

Connect once. Use FlowInbox from any agent: **Claude Desktop** (stdio), **Cursor** (stdio), or **Codex / CI / Cron** (Streamable HTTP + JWT Bearer token).

---

## 1. Claude Desktop (`claude_desktop_config.json`)

Add the following to your `claude_desktop_config.json` (located at `%APPDATA%\Claude\claude_desktop_config.json` on Windows or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "flowinbox": {
      "command": "python",
      "args": ["-m", "app.mcp.stdio_server"],
      "env": {
        "FLOWINBOX_LOCAL_USER_ID": "00000000-0000-0000-0000-000000000001",
        "PYTHONPATH": "<path-to-repository>/flowinbox/backend"
      }
    }
  }
}
```

---

## 2. Cursor IDE (`.cursor/mcp.json` or Global Settings)

Add the following configuration to Cursor MCP settings:

```json
{
  "mcpServers": {
    "flowinbox": {
      "command": "python",
      "args": ["-m", "app.mcp.stdio_server"],
      "env": {
        "FLOWINBOX_LOCAL_USER_ID": "00000000-0000-0000-0000-000000000001",
        "PYTHONPATH": "<path-to-repository>/flowinbox/backend"
      }
    }
  }
}
```

---

## 3. Codex / CI / Cron (Streamable HTTP Transport)

Invoke tools remotely over HTTP. Authenticate using a JWT Bearer token containing the user ID in the `sub` claim.

### Tool Invocation Example (`propose_send_email`)

```bash
curl -X POST http://localhost:8000/api/v1/mcp/tools/call \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "propose_send_email",
    "arguments": {
      "to_email": "recruiter@company.com",
      "subject": "Follow up application",
      "body": "Hi, checking on the status of my application."
    }
  }'
```

### Expected Response

```json
{
  "result": {
    "approval_id": "8f3e21a0-1234-4a2b-9876-abc123def456",
    "status": "pending",
    "action_type": "send_email",
    "message": "Created a pending approval; does not send. The user must approve via FlowInbox UI or POST /approvals/{id}/approve before anything is sent."
  }
}
```

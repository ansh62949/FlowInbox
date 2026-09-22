import pytest
import uuid
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.db.base import Base
from app.models.agent import Approval
from app.core.security import create_access_token

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.mark.asyncio
async def test_mcp_propose_send_email_creates_pending_approval_and_does_not_execute_tool():
    """Verify that calling propose_send_email over MCP HTTP creates a pending Approval DB row and never calls send_email_func."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_user_id = str(uuid.uuid4())
    jwt_token = create_access_token(subject=test_user_id)

    payload = {
        "name": "propose_send_email",
        "arguments": {
            "to_email": "recruiter@company.com",
            "subject": "Follow up application",
            "body": "Hi, checking on status."
        }
    }

    headers = {"Authorization": f"Bearer {jwt_token}"}

    with patch("app.mcp.tools.AsyncSessionLocal", TestingSessionLocal), \
         patch("app.tools.email_tools.send_email_func", new_callable=AsyncMock) as mock_send_email:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post("/api/v1/mcp/tools/call", json=payload, headers=headers)

        assert res.status_code == 200
        data = res.json()

        # 1. Assert response status is "pending" and contains approval_id
        assert data["result"]["status"] == "pending"
        approval_id = data["result"]["approval_id"]
        assert approval_id is not None

        # 2. Assert send_email_func tool execution was NOT invoked
        mock_send_email.assert_not_called()

        # 3. Assert Approval record exists in DB with status "pending"
        async with TestingSessionLocal() as db:
            appr = await db.get(Approval, uuid.UUID(approval_id))
            assert appr is not None
            assert appr.status == "pending"
            assert appr.action_type == "send_email"
            assert appr.payload["recipient"] == "recruiter@company.com"


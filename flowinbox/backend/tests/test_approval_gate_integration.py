from sqlalchemy import select
import pytest
import uuid
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from app.models.agent import Approval, AgentRun
from app.tools.base import ToolOutput
from app.core.security import create_access_token
from tests.conftest import get_test_db, TestingSessionLocal


@pytest.mark.asyncio
async def test_approval_gate_reject_flow():
    """Submit task -> Get approval ID -> Reject via API -> Assert DB state 'rejected' & tool NOT called."""
    async with TestingSessionLocal() as session:
        user = User(email="test_appr_reject@example.com", full_name="Test Reject User")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

    token = create_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Submit task resulting in send_email proposal
        res = await client.post("/api/v1/agent/tasks", json={
            "user_id": str(user_id),
            "request": "Find recruiters I contacted >5 days ago and send follow-up email"
        }, headers=headers)
        assert res.status_code == 200
        task_data = res.json()
        assert task_data["status"] == "waiting_approval"
        assert task_data["approval_status"] == "pending"

        task_id = task_data["task_id"]

        # 2. Fetch created Approval ID from DB
        async with TestingSessionLocal() as db:
            stmt = await db.execute(
                select(Approval).where(Approval.agent_run_id == uuid.UUID(task_id))
            )
            appr_row = stmt.scalar_one_or_none()
            assert appr_row is not None
            appr_id = str(appr_row.id)

        # 3. Patch send_email_func to assert zero invocations on reject
        with patch("app.api.v1.approvals.send_email_func", new_callable=AsyncMock) as mock_send:
            reject_res = await client.post(f"/api/v1/approvals/{appr_id}/reject", headers=headers)
            assert reject_res.status_code == 200
            assert reject_res.json()["status"] == "rejected"
            assert reject_res.json()["executed"] is False
            assert mock_send.call_count == 0

        # 4. Verify DB Approval record updated to 'rejected'
        async with TestingSessionLocal() as db:
            updated_appr = await db.get(Approval, uuid.UUID(appr_id))
            assert updated_appr.status == "rejected"


@pytest.mark.asyncio
async def test_approval_gate_approve_flow():
    """Submit task -> Get approval ID -> Approve via API -> Assert DB state 'approved' & tool WAS called."""
    async with TestingSessionLocal() as session:
        user = User(email="test_appr_approve@example.com", full_name="Test Approve User")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

    token = create_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.post("/api/v1/agent/tasks", json={
            "user_id": str(user_id),
            "request": "Find recruiters I contacted >5 days ago and send follow-up email"
        }, headers=headers)
        assert res.status_code == 200
        task_id = res.json()["task_id"]

        async with TestingSessionLocal() as db:
            stmt = await db.execute(
                select(Approval).where(Approval.agent_run_id == uuid.UUID(task_id))
            )
            appr_row = stmt.scalar_one_or_none()
            assert appr_row is not None
            appr_id = str(appr_row.id)

        # Patch send_email_func to assert EXACTLY ONCE invocation on approve
        with patch("app.api.v1.approvals.send_email_func", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = ToolOutput(
                success=True,
                data={"sent": True, "message_id": "msg_test_123"}
            )
            approve_res = await client.post(f"/api/v1/approvals/{appr_id}/approve", headers=headers)
            assert approve_res.status_code == 200
            assert approve_res.json()["status"] == "approved"
            assert approve_res.json()["executed"] is True
            assert mock_send.call_count == 1

        async with TestingSessionLocal() as db:
            updated_appr = await db.get(Approval, uuid.UUID(appr_id))
            assert updated_appr.status == "approved"


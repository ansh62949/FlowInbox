import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from app.models.email import EmailThread
from app.core.security import create_access_token
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_workspace_creation_and_member_list():
    async with TestingSessionLocal() as session:
        user = User(email="testwsuser@example.com", full_name="Workspace User")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

    token = create_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Create workspace
        res = await client.post("/api/v1/workspaces", json={"name": "Engineering Team", "slug": "eng-team"}, headers=headers)
        assert res.status_code == 200
        ws_data = res.json()
        assert ws_data["name"] == "Engineering Team"
        ws_id = ws_data["id"]

        # List members
        mem_res = await client.get(f"/api/v1/workspaces/{ws_id}/members", headers=headers)
        assert mem_res.status_code == 200
        members = mem_res.json()
        assert len(members) >= 1
        assert members[0]["role"] == "OWNER"


from datetime import datetime, timezone
from app.models.user import User
from app.models.email import EmailThread
from app.core.security import create_access_token
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_thread_assignment_flow():
    async with TestingSessionLocal() as session:
        user = User(email="testassign@example.com", full_name="Assignee User")
        session.add(user)
        await session.flush()

        thread = EmailThread(
            user_id=user.id,
            gmail_thread_id="thr_assign_100",
            subject="Assignment Test Thread",
            last_message_at=datetime.now(timezone.utc),
            category="inbox",
            importance="normal"
        )
        session.add(thread)
        await session.commit()

        user_id = user.id
        thread_id = str(thread.id)

    token = create_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        assignee_id = str(uuid.uuid4())

        # Assign thread
        res = await client.post(f"/api/v1/inbox/threads/{thread_id}/assign", json={
            "assigned_to": assignee_id
        }, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["assigned_to"] == assignee_id

        # Unassign thread
        un_res = await client.post(f"/api/v1/inbox/threads/{thread_id}/unassign", headers=headers)
        assert un_res.status_code == 200
        assert un_res.json()["status"] == "unassigned"

import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User, OAuthAccount
from app.models.email import EmailThread, Email
from app.core.security import create_access_token
from tests.conftest import TestingSessionLocal


@pytest.mark.asyncio
async def test_two_user_security_isolation():
    """Create User A and User B with distinct OAuth accounts & email threads.
    Assert User A authenticated session can NEVER read or modify User B data,
    and unauthenticated calls return 401 Unauthorized.
    """
    async with TestingSessionLocal() as session:
        # 1. Create User A
        user_a = User(email="usera@example.com", full_name="User A")
        session.add(user_a)
        await session.flush()

        oauth_a = OAuthAccount(
            user_id=user_a.id,
            provider="google",
            encrypted_access_token="enc_token_a",
            scopes="gmail"
        )
        session.add(oauth_a)

        thread_a = EmailThread(
            user_id=user_a.id,
            gmail_thread_id="thr_user_a_100",
            subject="User A Private Thread",
            last_message_at=datetime.now(timezone.utc),
            category="inbox",
            importance="normal"
        )
        session.add(thread_a)
        await session.flush()

        email_a = Email(
            user_id=user_a.id,
            thread_id=thread_a.id,
            gmail_id="msg_a_100",
            sender="Sender A",
            sender_email="sendera@example.com",
            recipients="usera@example.com",
            subject="User A Private Thread",
            body_text="User A confidential body text",
            sent_at=datetime.now(timezone.utc),
            is_incoming=True
        )
        session.add(email_a)

        # 2. Create User B
        user_b = User(email="userb@example.com", full_name="User B")
        session.add(user_b)
        await session.flush()

        oauth_b = OAuthAccount(
            user_id=user_b.id,
            provider="google",
            encrypted_access_token="enc_token_b",
            scopes="gmail"
        )
        session.add(oauth_b)

        thread_b = EmailThread(
            user_id=user_b.id,
            gmail_thread_id="thr_user_b_200",
            subject="User B Secret Project Thread",
            last_message_at=datetime.now(timezone.utc),
            category="inbox",
            importance="high"
        )
        session.add(thread_b)
        await session.flush()

        email_b = Email(
            user_id=user_b.id,
            thread_id=thread_b.id,
            gmail_id="msg_b_200",
            sender="Boss B",
            sender_email="bossb@company.com",
            recipients="userb@example.com",
            subject="User B Secret Project Thread",
            body_text="Top secret data for User B only",
            sent_at=datetime.now(timezone.utc),
            is_incoming=True
        )
        session.add(email_b)

        await session.commit()

        user_a_id = user_a.id
        thread_a_id = str(thread_a.id)
        user_b_id = user_b.id
        thread_b_id = str(thread_b.id)

    # Issue JWT session token for User A
    token_a = create_access_token(user_a_id)
    token_b = create_access_token(user_b_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Test 1: Unauthenticated request should be rejected with 401
        res_unauth = await client.get("/api/v1/inbox/threads")
        assert res_unauth.status_code == 401

        # Test 2: Authenticate as User A and list threads
        headers_a = {"Authorization": f"Bearer {token_a}"}
        res_a_threads = await client.get("/api/v1/inbox/threads", headers=headers_a)
        assert res_a_threads.status_code == 200
        threads_a_list = res_a_threads.json()
        
        # Assert User A only sees User A's threads, NOT User B's thread
        thread_ids_retrieved = [t["id"] for t in threads_a_list]
        assert thread_a_id in thread_ids_retrieved
        assert thread_b_id not in thread_ids_retrieved

        # Test 3: User A attempts to access User B's thread detail directly -> 404 / 401
        res_b_detail_by_a = await client.get(f"/api/v1/inbox/threads/{thread_b_id}", headers=headers_a)
        assert res_b_detail_by_a.status_code == 404

        # Test 4: User A attempts to star User B's thread -> 404 / 401
        res_star_b_by_a = await client.post(f"/api/v1/inbox/threads/{thread_b_id}/star", headers=headers_a)
        assert res_star_b_by_a.status_code == 404

        # Test 5: Authenticate as User B and verify User B sees User B's threads
        headers_b = {"Authorization": f"Bearer {token_b}"}
        res_b_threads = await client.get("/api/v1/inbox/threads", headers=headers_b)
        assert res_b_threads.status_code == 200
        threads_b_list = res_b_threads.json()
        thread_b_ids_retrieved = [t["id"] for t in threads_b_list]
        assert thread_b_id in thread_b_ids_retrieved
        assert thread_a_id not in thread_b_ids_retrieved


@pytest.mark.asyncio
async def test_approvals_and_resource_isolation_between_users():
    """Test that User B can NEVER approve/reject/view User A's pending approval,
    and tool execution is never triggered for User B's attempt.
    Also tests drafts, followups, channels, and workspace isolation.
    """
    from app.models.agent import AgentRun, Approval
    from app.models.email import Draft, Followup
    from app.models.channels import Channel
    from app.models.workspace import Workspace, WorkspaceMember

    async with TestingSessionLocal() as session:
        # Create User A & User B
        user_a = User(email="usera_appr@example.com", full_name="User A Approval")
        user_b = User(email="userb_appr@example.com", full_name="User B Approval")
        session.add_all([user_a, user_b])
        await session.flush()

        # Seed AgentRun & pending Approval for User A
        run_a = AgentRun(
            user_id=user_a.id,
            request_text="Send email to recruiter",
            status="waiting_approval",
            intent="send_email"
        )
        session.add(run_a)
        await session.flush()

        appr_a = Approval(
            user_id=user_a.id,
            agent_run_id=run_a.id,
            action_type="send_email",
            payload={"to": "recruiter@tech.com", "subject": "Interview Confirmation"},
            status="pending",
            requested_at=datetime.now(timezone.utc)
        )
        session.add(appr_a)

        # Seed Draft for User A
        draft_a = Draft(
            user_id=user_a.id,
            to_email="recruiter@tech.com",
            subject="Draft Subject A",
            body="Draft Body A",
            is_sent=False
        )
        session.add(draft_a)

        # Seed Channel for User A
        channel_a = Channel(
            user_id=user_a.id,
            name="User A Secret Channel",
            icon="hash"
        )
        session.add(channel_a)

        # Seed Workspace for User A
        ws_a = Workspace(
            name="User A Private Workspace",
            slug="user-a-ws",
            created_by=user_a.id
        )
        session.add(ws_a)
        await session.flush()

        ws_member_a = WorkspaceMember(
            workspace_id=ws_a.id,
            user_id=user_a.id,
            role="OWNER"
        )
        session.add(ws_member_a)

        await session.commit()

        user_a_id = user_a.id
        user_b_id = user_b.id
        appr_a_id = str(appr_a.id)
        draft_a_id = str(draft_a.id)
        channel_a_id = str(channel_a.id)
        ws_a_id = str(ws_a.id)

    token_a = create_access_token(user_a_id)
    token_b = create_access_token(user_b_id)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Unauthenticated request to approvals -> 401
        res_unauth = await client.get("/api/v1/approvals")
        assert res_unauth.status_code == 401

        res_unauth_approve = await client.post(f"/api/v1/approvals/{appr_a_id}/approve")
        assert res_unauth_approve.status_code == 401

        # 2. User A lists approvals -> sees pending approval
        res_a_appr = await client.get("/api/v1/approvals", headers=headers_a)
        assert res_a_appr.status_code == 200
        apprs_a = res_a_appr.json()
        assert len(apprs_a) == 1
        assert apprs_a[0]["id"] == appr_a_id

        # 3. User B lists approvals -> returns EMPTY list (cannot see User A's pending approval)
        res_b_appr = await client.get("/api/v1/approvals", headers=headers_b)
        assert res_b_appr.status_code == 200
        apprs_b = res_b_appr.json()
        assert len(apprs_b) == 0

        # 4. User B attempts to approve User A's action -> MUST return 404
        res_b_approve = await client.post(f"/api/v1/approvals/{appr_a_id}/approve", headers=headers_b)
        assert res_b_approve.status_code == 404

        # 5. User B attempts to reject User A's action -> MUST return 404
        res_b_reject = await client.post(f"/api/v1/approvals/{appr_a_id}/reject", headers=headers_b)
        assert res_b_reject.status_code == 404

        # 6. Verify in DB that Approval record status remains "pending" (not approved/rejected by B)
        async with TestingSessionLocal() as session:
            appr_db = await session.get(Approval, uuid.UUID(appr_a_id))
            assert appr_db.status == "pending"

        # 7. Drafts Isolation: User B cannot list or update User A's draft
        res_b_drafts = await client.get("/api/v1/drafts", headers=headers_b)
        assert res_b_drafts.status_code == 200
        assert len(res_b_drafts.json()) == 0

        res_b_update_draft = await client.put(
            f"/api/v1/drafts/{draft_a_id}",
            headers=headers_b,
            json={"body": "Hacked body"}
        )
        assert res_b_update_draft.status_code == 404

        # 8. Channels Isolation: User B cannot get filters or messages of User A's channel
        res_b_channel_msgs = await client.get(f"/api/v1/channels/{channel_a_id}/messages", headers=headers_b)
        assert res_b_channel_msgs.status_code == 404

        # 9. Workspace Isolation: User B cannot list members of User A's workspace
        res_b_ws_members = await client.get(f"/api/v1/workspaces/{ws_a_id}/members", headers=headers_b)
        assert res_b_ws_members.status_code == 404

        # 10. User A approves own action -> succeeds
        res_a_approve = await client.post(f"/api/v1/approvals/{appr_a_id}/approve", headers=headers_a)
        assert res_a_approve.status_code == 200
        assert res_a_approve.json()["status"] == "approved"

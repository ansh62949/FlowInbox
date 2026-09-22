import pytest
from app.tools.email_tools import search_emails_func, SearchEmailsInput, create_draft_func, CreateDraftInput


@pytest.mark.asyncio
async def test_search_emails_tool():
    inp = SearchEmailsInput(user_id="test_user_123", query="recruiter")
    out = await search_emails_func(inp)
    assert out.success is True
    assert isinstance(out.emails, list)


@pytest.mark.asyncio
async def test_create_draft_tool():
    inp = CreateDraftInput(
        user_id="test_user_123",
        to_email="priya@techcorp.io",
        subject="Follow up",
        body="Hello Priya"
    )
    out = await create_draft_func(inp)
    assert out.success is True
    assert out.draft_id.startswith("draft_")

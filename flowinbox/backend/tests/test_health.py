import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test root endpoint returns welcome message or SPA HTML index."""
    response = await async_client.get("/")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        data = response.json()
        assert "message" in data
    else:
        assert "<html" in response.text.lower()



@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    """Test health check endpoint structure."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "project" in data
    assert data["project"] == "FlowInbox AI"


@pytest.mark.asyncio
async def test_health_check_head_endpoint(async_client: AsyncClient):
    """Test health check endpoint accepts HEAD requests for uptime monitors."""
    response = await async_client.head("/api/v1/health")
    assert response.status_code == 200


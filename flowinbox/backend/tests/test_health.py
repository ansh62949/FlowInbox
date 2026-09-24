import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test root endpoint returns welcome message."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Welcome to FlowInbox AI API"


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


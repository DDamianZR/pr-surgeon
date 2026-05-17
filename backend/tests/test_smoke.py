"""
Smoke tests for PR Surgeon API.
Basic tests to verify the API is running and endpoints respond correctly.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_root_endpoint() -> None:
    """Test that the root endpoint returns expected status and version."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PR Surgeon API alive"
        assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """Test that the health check endpoint returns 200 and expected structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "github_configured" in data
        assert "llm_mode" in data
        assert isinstance(data["github_configured"], bool)
        assert isinstance(data["llm_mode"], str)


@pytest.mark.asyncio
async def test_health_endpoint_structure() -> None:
    """Test that health endpoint returns all required fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        
        data = response.json()
        required_fields = ["status", "github_configured", "llm_mode"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

# Made with Bob

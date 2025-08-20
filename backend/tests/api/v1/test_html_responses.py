import pytest
import pytest_asyncio
from httpx import AsyncClient
import re
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_api_error_responses_contain_detail(client: AsyncClient):
    """Test that API error responses contain proper error details."""
    # Test authentication error with malformed token
    response = await client.get(
        "/api/v1/users/me",  # Requires valid authentication
        headers={
            "Authorization": "Bearer invalid.token.here",
        }
    )
    assert response.status_code == 401
    
    # Verify the response contains error information
    if "application/json" in response.headers.get("content-type", ""):
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], str)
    else:
        # If not JSON, check response text
        response_text = response.text.lower()
        assert any(word in response_text for word in ["unauthorized", "authentication", "token", "invalid"])

@pytest.mark.asyncio
async def test_invalid_login_error_response(client: AsyncClient):
    """Test error response for invalid login credentials."""
    # Submit invalid login credentials
    response = await client.post(
        "/api/v1/users/login",
        data={
            "username": "nonexistent",
            "password": "wrong"
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )
    assert response.status_code == 401
    
    # Verify proper error response
    if "application/json" in response.headers.get("content-type", ""):
        error = response.json()
        assert "detail" in error
        assert isinstance(error["detail"], str)
    else:
        # If HTML error message, verify it contains error info
        assert "text/html" in response.headers.get("content-type", "")
        response_text = response.text.lower()
        assert any(word in response_text for word in ["error", "invalid", "unauthorized", "incorrect"])

@pytest.mark.asyncio
async def test_chores_api_response_structure(client: AsyncClient, parent_token, test_chore):
    """Test the structure of chores API response."""
    response = await client.get(
        "/api/v1/chores/",
        headers={
            "Authorization": f"Bearer {parent_token}",
        }
    )
    assert response.status_code == 200
    
    # Verify it's JSON
    assert "application/json" in response.headers["content-type"]
    
    # Parse JSON response
    chores_data = response.json()
    assert isinstance(chores_data, list)
    
    # If chores exist, verify structure
    if chores_data:
        chore = chores_data[0]
        required_fields = ["id", "title", "reward", "is_completed", "is_approved"]
        for field in required_fields:
            assert field in chore, f"Missing required field: {field}"

@pytest.mark.asyncio
async def test_root_endpoint_response(client: AsyncClient):
    """Test the root endpoint returns proper API information."""
    response = await client.get("/")
    assert response.status_code == 200
    
    # Verify it's JSON
    assert "application/json" in response.headers["content-type"]
    
    # Parse JSON
    data = response.json()
    assert isinstance(data, dict)
    
    # Check for expected fields
    expected_fields = ["name", "version", "status", "docs"]
    for field in expected_fields:
        assert field in data, f"Missing expected field: {field}"

@pytest.mark.asyncio
async def test_health_endpoint_response(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    
    # Verify it's JSON
    assert "application/json" in response.headers["content-type"]
    
    # Parse JSON
    health_data = response.json()
    assert isinstance(health_data, dict)
    assert "status" in health_data
    assert health_data["status"] in ["healthy", "unhealthy"]
    
    if health_data["status"] == "healthy":
        assert "database" in health_data
        assert health_data["database"] == "connected"
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint returns API information."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert "name" in data
    assert "Chores Tracker" in data["name"]

@pytest.mark.asyncio 
async def test_nonexistent_routes_return_404(client: AsyncClient):
    """Test that non-existent routes return 404."""
    # These routes don't exist in the pure API backend
    routes_to_test = ["/dashboard", "/pages/login", "/components/chore_list"]
    
    for route in routes_to_test:
        response = await client.get(route)
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_users_me_endpoint(client: AsyncClient, parent_token):
    """Test the users/me endpoint returns the current user."""
    response = await client.get(
        "/api/v1/users/me", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert data["is_parent"] == True

@pytest.mark.asyncio
async def test_api_endpoints_that_exist(client: AsyncClient, parent_token, test_child_user, test_chore):
    """Test API endpoints that actually exist in the system."""
    
    # Test chores endpoint (this should exist)
    response = await client.get(
        "/api/v1/chores", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    assert isinstance(data, list)
    
    # Test users/me endpoint 
    response = await client.get(
        "/api/v1/users/me", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    assert "id" in data
    assert "username" in data

@pytest.mark.asyncio 
async def test_nonexistent_api_endpoints_return_404(client: AsyncClient, parent_token):
    """Test that non-implemented API endpoints return 404."""
    non_existent_endpoints = [
        "/api/v1/users/children",
        "/api/v1/users/children-cards", 
        "/api/v1/users/summary",
        "/pages/user-form"
    ]
    
    for endpoint in non_existent_endpoints:
        response = await client.get(
            endpoint,
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        assert response.status_code == 404 
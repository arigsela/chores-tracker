"""Tests for v2 user endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_register_parent_v2(
    async_client: AsyncClient,
    test_db: AsyncSession
):
    """Test parent registration with v2 endpoint."""
    response = await async_client.post(
        "/api/v2/users/register",
        json={
            "username": "newparent",
            "password": "SecurePass123!",
            "email": "newparent@example.com",
            "is_parent": True
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Check standardized response format
    assert data["success"] is True
    assert data["data"]["username"] == "newparent"
    assert data["data"]["email"] == "newparent@example.com"
    assert data["data"]["is_parent"] is True
    assert data["error"] is None


@pytest.mark.asyncio
async def test_register_child_v2(
    async_client: AsyncClient,
    test_db: AsyncSession,
    test_parent_user: User,
    parent_headers: dict
):
    """Test child registration with v2 endpoint."""
    response = await async_client.post(
        "/api/v2/users/register",
        json={
            "username": "newchild",
            "password": "ChildPass123!",
            "is_parent": False
        },
        headers=parent_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["username"] == "newchild"
    assert data["data"]["is_parent"] is False
    assert data["data"]["parent_id"] == test_parent_user.id


@pytest.mark.asyncio
async def test_get_current_user_v2(
    async_client: AsyncClient,
    test_parent_user: User,
    parent_headers: dict
):
    """Test getting current user with v2 endpoint."""
    response = await async_client.get(
        "/api/v2/users/me",
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["id"] == test_parent_user.id
    assert data["data"]["username"] == test_parent_user.username


@pytest.mark.asyncio
async def test_list_users_v2(
    async_client: AsyncClient,
    test_parent_user: User,
    test_child_user: User,
    parent_headers: dict
):
    """Test listing users with v2 endpoint."""
    response = await async_client.get(
        "/api/v2/users/",
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check paginated response format
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert data["total"] >= 2
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] >= 1


@pytest.mark.asyncio
async def test_get_children_v2(
    async_client: AsyncClient,
    test_parent_user: User,
    test_child_user: User,
    parent_headers: dict
):
    """Test getting children for parent with v2 endpoint."""
    response = await async_client.get(
        "/api/v2/users/children",
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1
    assert any(child["id"] == test_child_user.id for child in data["data"])


@pytest.mark.asyncio
async def test_update_user_v2(
    async_client: AsyncClient,
    test_child_user: User,
    parent_headers: dict
):
    """Test updating user with v2 endpoint."""
    response = await async_client.put(
        f"/api/v2/users/{test_child_user.id}",
        json={"email": "updated@example.com"},
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_reset_password_v2(
    async_client: AsyncClient,
    test_child_user: User,
    parent_headers: dict
):
    """Test resetting child password with v2 endpoint."""
    response = await async_client.post(
        f"/api/v2/users/{test_child_user.id}/reset-password",
        json={"new_password": "NewSecurePass123!"},
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["message"] == "Password reset successfully"
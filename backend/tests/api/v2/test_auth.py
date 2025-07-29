"""Tests for v2 authentication endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security.password import get_password_hash


@pytest.mark.asyncio
async def test_login_v2_success(
    async_client: AsyncClient,
    test_db: AsyncSession,
    test_parent_user: User
):
    """Test successful login with v2 endpoint."""
    # Login with form data (OAuth2 standard)
    response = await async_client.post(
        "/api/v2/auth/login",
        data={
            "username": test_parent_user.username,
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check standardized response format
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["access_token"]
    assert data["data"]["token_type"] == "bearer"
    assert data["error"] is None
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_login_v2_invalid_credentials(
    async_client: AsyncClient,
    test_db: AsyncSession,
    test_parent_user: User
):
    """Test login with invalid credentials."""
    response = await async_client.post(
        "/api/v2/auth/login",
        data={
            "username": test_parent_user.username,
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check error response format
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"] == "Incorrect username or password"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_login_v2_missing_fields(
    async_client: AsyncClient
):
    """Test login with missing fields."""
    response = await async_client.post(
        "/api/v2/auth/login",
        data={"username": "test"}  # Missing password
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_v2_nonexistent_user(
    async_client: AsyncClient
):
    """Test login with non-existent user."""
    response = await async_client.post(
        "/api/v2/auth/login",
        data={
            "username": "doesnotexist",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert data["error"] == "Incorrect username or password"
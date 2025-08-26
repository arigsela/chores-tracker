"""
Test that HTML endpoints return 404 since we converted to REST API.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.core.security.password import get_password_hash
from backend.app.core.security.jwt import create_access_token


async def create_test_user_with_token(db_session: AsyncSession, username: str = "testuser"):
    """Helper to create a test user and return user and token."""
    user = User(
        username=username,
        email=f"{username}@test.com",
        hashed_password=get_password_hash("testpassword"),
        is_parent=True,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    token = create_access_token(subject=str(user.id))
    return user, token


class TestHTMLEndpoints:
    """Test that non-existent HTML endpoints return 404 since we converted to REST API."""
    
    @pytest.mark.asyncio
    async def test_nonexistent_html_endpoints_return_404(self, client: AsyncClient):
        """Test that all old HTML endpoints return 404."""
        html_endpoints_that_no_longer_exist = [
            "/reports",
            "/dashboard", 
            "/pages/login",
            "/components/success",
            "/components/error",
            "/api/v1/html/users/children",
            "/api/v1/html/chores/child/1",
            "/api/v1/html/chores/completed",
            "/api/v1/html/chores/1/approve",
            "/api/v1/html/chores/1/edit",
            "/api/v1/html/children/1/reset-password",
            "/api/v1/html/components/pending-approval",
            "/api/v1/html/components/success-message",
            "/api/v1/html/components/error-message"
        ]
        
        for endpoint in html_endpoints_that_no_longer_exist:
            response = await client.get(endpoint)
            assert response.status_code == 404, f"Endpoint {endpoint} should return 404 but returned {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_actual_api_endpoints_work(self, client: AsyncClient, db_session: AsyncSession):
        """Test that the actual REST API endpoints work correctly."""
        # Create test user with token
        user, token = await create_test_user_with_token(db_session, "testparent")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test that actual API endpoints work
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        response = await client.get("/api/v1/chores", headers=headers)  
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        response = await client.get("/api/v1/users/my-children", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio 
    async def test_root_and_health_endpoints_work(self, client: AsyncClient):
        """Test that the basic endpoints still work."""
        # Root endpoint should return JSON
        response = await client.get("/")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        data = response.json()
        assert "name" in data
        assert "version" in data
        
        # Health endpoint should return JSON
        response = await client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        data = response.json()
        assert "status" in data
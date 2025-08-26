"""
Test that more HTML endpoints return 404 since we converted to REST API.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.core.security.password import get_password_hash
from backend.app.core.security.jwt import create_access_token


class TestMainHTMLEndpoints:
    """Test that non-existent HTML endpoints return 404 since we converted to REST API."""
    
    @pytest.mark.asyncio
    async def test_more_nonexistent_html_endpoints_return_404(self, client: AsyncClient):
        """Test that additional old HTML endpoints return 404."""
        html_endpoints_that_no_longer_exist = [
            "/reports",
            "/pages/login",  
            "/pages/register",
            "/users/children-cards",
            "/users/summary",
            "/chores",
            "/chores/available",
            "/chores/pending-approval",
            "/chores/active",
            "/chores/completed",
            "/api/v1/html/chores/approve",
            "/api/v1/html/chores/disable"
        ]
        
        for endpoint in html_endpoints_that_no_longer_exist:
            response = await client.get(endpoint)
            assert response.status_code == 404, f"Endpoint {endpoint} should return 404 but returned {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_approve_chore_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test that approve chore endpoint returns 404 - this functionality moved to REST API."""
        # Create test user
        user = User(
            username="testparent", 
            email="testparent@test.com",
            hashed_password=get_password_hash("testpassword"),
            is_parent=True,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create test chore
        chore = Chore(
            title="Test Chore",
            description="A test chore", 
            reward=5.0,
            cooldown_days=1,
            is_recurring=False,
            is_completed=True,  # Completed but not approved
            is_approved=False,
            is_disabled=False,
            assignee_id=user.id,
            creator_id=user.id,
            is_range_reward=False
        )
        db_session.add(chore)
        await db_session.commit()
        await db_session.refresh(chore)
        
        # HTML approve endpoint should return 404
        response = await client.post(f"/api/v1/html/chores/{chore.id}/approve")
        assert response.status_code == 404
    
    @pytest.mark.asyncio 
    async def test_disable_chore_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test that disable chore endpoint returns 404 - this functionality moved to REST API."""
        # Create test user
        user = User(
            username="testparent2",
            email="testparent2@test.com", 
            hashed_password=get_password_hash("testpassword"),
            is_parent=True,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create test chore
        chore = Chore(
            title="Test Chore 2",
            description="Another test chore",
            reward=3.0,
            cooldown_days=1, 
            is_recurring=False,
            is_completed=False,
            is_approved=False,
            is_disabled=False,
            assignee_id=user.id,
            creator_id=user.id,
            is_range_reward=False
        )
        db_session.add(chore)
        await db_session.commit()
        await db_session.refresh(chore)
        
        # HTML disable endpoint should return 404
        response = await client.post(f"/api/v1/html/chores/{chore.id}/disable")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_rest_api_chore_endpoints_work(self, client: AsyncClient, db_session: AsyncSession):
        """Test that the actual REST API chore endpoints work correctly."""
        # Create test user  
        user = User(
            username="testparent3",
            email="testparent3@test.com",
            hashed_password=get_password_hash("testpassword"), 
            is_parent=True,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        token = create_access_token(subject=str(user.id))
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test that actual REST API endpoints work
        response = await client.get("/api/v1/chores", headers=headers)
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        
        # Test parent-specific endpoint
        response = await client.get("/api/v1/chores/pending-approval", headers=headers)
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        
        # Test that child-only endpoint returns 403 for parents
        response = await client.get("/api/v1/chores/available", headers=headers)
        assert response.status_code == 403  # Parent can't access child-only endpoint
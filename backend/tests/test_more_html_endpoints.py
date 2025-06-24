"""
Test more HTML endpoints in main.py.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.core.security.password import get_password_hash
from backend.app.core.security.jwt import create_access_token


class TestMainHTMLEndpoints:
    """Test HTML endpoints defined in main.py."""
    
    @pytest.mark.asyncio
    async def test_reports_page(self, client: AsyncClient):
        """Test the reports page endpoint."""
        response = await client.get("/reports")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_page_route_login(self, client: AsyncClient):
        """Test generic page route with login page."""
        response = await client.get("/pages/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_page_route_register(self, client: AsyncClient):
        """Test generic page route with register page."""
        response = await client.get("/pages/register")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_page_route_not_found(self, client: AsyncClient):
        """Test generic page route with non-existent page."""
        response = await client.get("/pages/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_users_children_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test users children list endpoint."""
        # Create parent
        parent = User(
            username="parent_children_list",
            email="parent_cl@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        token = create_access_token(subject=str(parent.id))
        
        response = await client.get(
            "/api/v1/users/children",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_users_summary_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test users summary endpoint."""
        # Create parent
        parent = User(
            username="parent_summary",
            email="parent_sum@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        token = create_access_token(subject=str(parent.id))
        
        response = await client.get(
            "/api/v1/users/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_chores_html_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test chores HTML endpoint."""
        # Create parent
        parent = User(
            username="parent_chores_html",
            email="parent_ch@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        token = create_access_token(subject=str(parent.id))
        
        response = await client.get(
            "/api/v1/chores",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_available_chores_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test available chores endpoint."""
        # Create parent and child
        parent = User(
            username="parent_avail",
            email="parent_av@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_avail",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        child_token = create_access_token(subject=str(child.id))
        
        response = await client.get(
            "/api/v1/html/chores/available",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_pending_chores_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test pending chores endpoint."""
        # Create parent
        parent = User(
            username="parent_pending",
            email="parent_pend@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        parent_token = create_access_token(subject=str(parent.id))
        
        response = await client.get(
            "/api/v1/html/chores/pending",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_active_chores_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test active chores endpoint."""
        # Create parent
        parent = User(
            username="parent_active",
            email="parent_act@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        parent_token = create_access_token(subject=str(parent.id))
        
        response = await client.get(
            "/api/v1/html/chores/active",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_completed_chores_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test completed chores endpoint for parent."""
        # Create parent
        parent = User(
            username="parent_completed",
            email="parent_comp@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        parent_token = create_access_token(subject=str(parent.id))
        
        response = await client.get(
            "/api/v1/html/chores/completed",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_complete_chore_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test complete chore endpoint."""
        # Create parent and child
        parent = User(
            username="parent_comp_chore",
            email="parent_cc@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_comp_chore",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        # Create a chore
        chore = Chore(
            title="Test Chore",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        db_session.add(chore)
        await db_session.commit()
        
        child_token = create_access_token(subject=str(child.id))
        
        response = await client.post(
            f"/api/v1/chores/{chore.id}/complete",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_approve_chore_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test approve chore endpoint."""
        # Create parent and child
        parent = User(
            username="parent_app_chore",
            email="parent_ac@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_app_chore",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        # Create a completed chore
        chore = Chore(
            title="Test Approve Chore",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=True,  # Already completed
            is_approved=False,
            is_disabled=False
        )
        db_session.add(chore)
        await db_session.commit()
        
        parent_token = create_access_token(subject=str(parent.id))
        
        response = await client.post(
            f"/api/v1/chores/{chore.id}/approve",
            headers={"Authorization": f"Bearer {parent_token}"},
            json={"is_approved": True, "reward_value": 5.0}
        )
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_disable_chore_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """Test disable chore endpoint."""
        # Create parent
        parent = User(
            username="parent_dis_chore",
            email="parent_dc@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        # Create a chore
        chore = Chore(
            title="Test Disable Chore",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=None,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        db_session.add(chore)
        await db_session.commit()
        
        parent_token = create_access_token(subject=str(parent.id))
        
        # Refresh chore to get ID
        await db_session.refresh(chore)
        
        response = await client.post(
            f"/api/v1/chores/{chore.id}/disable",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        assert response.status_code == 200
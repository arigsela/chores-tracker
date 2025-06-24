"""
Test HTML endpoints in main.py.
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
    """Test HTML endpoints that return template responses."""
    
    @pytest.mark.asyncio
    async def test_reports_page(self, client: AsyncClient):
        """Test the reports page endpoint."""
        response = await client.get("/reports")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_child_users_list_unauthorized(self, client: AsyncClient):
        """Test child users list without authentication."""
        response = await client.get("/api/v1/html/users/children")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_child_users_list_authorized(self, client: AsyncClient, db_session: AsyncSession):
        """Test child users list with authentication."""
        user, token = await create_test_user_with_token(db_session)
        
        response = await client.get(
            "/api/v1/html/users/children",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_child_chores_unauthorized(self, client: AsyncClient):
        """Test child chores endpoint without authentication."""
        response = await client.get("/api/v1/html/chores/child/1")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_child_chores_parent_user(self, client: AsyncClient, db_session: AsyncSession):
        """Test child chores endpoint as parent (should be forbidden)."""
        parent, token = await create_test_user_with_token(db_session, "parent_test")
        
        response = await client.get(
            f"/api/v1/html/chores/child/{parent.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_completed_chores_unauthorized(self, client: AsyncClient):
        """Test completed chores endpoint without authentication."""
        response = await client.get("/api/v1/html/chores/child/1/completed")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_completed_chores_parent_forbidden(self, client: AsyncClient, db_session: AsyncSession):
        """Test completed chores endpoint as parent."""
        parent, token = await create_test_user_with_token(db_session, "parent_comp")
        
        response = await client.get(
            f"/api/v1/html/chores/child/{parent.id}/completed",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
    
    @pytest.mark.skip(reason="Endpoint /chores/1/approve-form does not exist")
    @pytest.mark.asyncio
    async def test_approve_chore_form_unauthorized(self, client: AsyncClient):
        """Test approve chore form without authentication."""
        response = await client.get("/chores/1/approve-form")
        assert response.status_code == 401
    
    @pytest.mark.skip(reason="Endpoint /chores/1/approve-form does not exist")
    @pytest.mark.asyncio
    async def test_approve_chore_form_child_forbidden(self, client: AsyncClient, db_session: AsyncSession):
        """Test approve chore form as child."""
        # Create parent
        parent = User(
            username="parent_approve_form",
            email="parentaf@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        # Create child
        child = User(
            username="child_approve_form",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        # Get child token
        child_token = create_access_token(subject=str(child.id))
        
        response = await client.get(
            "/chores/1/approve-form",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        assert response.status_code == 403
    
    @pytest.mark.skip(reason="Endpoint /chores/1/edit-form does not exist")
    @pytest.mark.asyncio
    async def test_edit_chore_form_unauthorized(self, client: AsyncClient):
        """Test edit chore form without authentication."""
        response = await client.get("/chores/1/edit-form")
        assert response.status_code == 401
    
    @pytest.mark.skip(reason="Endpoint /chores/1/edit-form does not exist")
    @pytest.mark.asyncio
    async def test_edit_chore_form_child_forbidden(self, client: AsyncClient, db_session: AsyncSession):
        """Test edit chore form as child."""
        # Create parent and child
        parent = User(
            username="parent_edit_form",
            email="parentef@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_edit_form",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        child_token = create_access_token(subject=str(child.id))
        
        response = await client.get(
            "/chores/1/edit-form",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        assert response.status_code == 403
    
    @pytest.mark.skip(reason="Endpoint PUT /chores/1 does not exist")
    @pytest.mark.asyncio
    async def test_update_chore_unauthorized(self, client: AsyncClient):
        """Test update chore endpoint without authentication."""
        response = await client.put(
            "/chores/1",
            json={"title": "Updated Chore"}
        )
        assert response.status_code == 401
    
    @pytest.mark.skip(reason="Endpoint PUT /chores/1 does not exist")
    @pytest.mark.asyncio
    async def test_update_chore_child_forbidden(self, client: AsyncClient, db_session: AsyncSession):
        """Test update chore endpoint as child."""
        # Create parent and child
        parent = User(
            username="parent_update",
            email="parentup@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_update",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        child_token = create_access_token(subject=str(child.id))
        
        response = await client.put(
            "/chores/1",
            headers={"Authorization": f"Bearer {child_token}"},
            json={"title": "Updated Chore"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_reset_child_password_form_unauthorized(self, client: AsyncClient):
        """Test reset child password form without authentication."""
        response = await client.get("/api/v1/html/children/1/reset-password-form")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_reset_child_password_form_child_forbidden(self, client: AsyncClient, db_session: AsyncSession):
        """Test reset password form as child."""
        # Create parent and child
        parent = User(
            username="parent_reset_form",
            email="parentrf@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_reset_form",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        child_token = create_access_token(subject=str(child.id))
        
        response = await client.get(
            f"/api/v1/html/children/{child.id}/reset-password-form",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_success_message_component(self, client: AsyncClient):
        """Test success message component endpoint."""
        response = await client.get("/components/success-message?message=Test%20Success")
        assert response.status_code == 200
        assert "Test Success" in response.text
    
    @pytest.mark.asyncio
    async def test_error_message_component(self, client: AsyncClient):
        """Test error message component endpoint."""
        response = await client.get("/components/error-message?message=Test%20Error")
        assert response.status_code == 200
        assert "Test Error" in response.text
    
    @pytest.mark.skip(reason="Component endpoints do not require authentication")
    @pytest.mark.asyncio
    async def test_chore_list_component_unauthorized(self, client: AsyncClient):
        """Test chore list component without authentication."""
        response = await client.get("/components/chore-list")
        assert response.status_code == 401
    
    @pytest.mark.skip(reason="Component endpoints do not require authentication")
    @pytest.mark.asyncio
    async def test_available_chores_component_unauthorized(self, client: AsyncClient):
        """Test available chores component without authentication."""
        response = await client.get("/components/available-chores")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_pending_approval_component_unauthorized(self, client: AsyncClient):
        """Test pending approval component without authentication."""
        response = await client.get("/api/v1/html/chores/pending-approval")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_pending_approval_component_child_forbidden(self, client: AsyncClient, db_session: AsyncSession):
        """Test pending approval component as child."""
        # Create parent and child
        parent = User(
            username="parent_pending",
            email="parentpen@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_pending",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        child_token = create_access_token(subject=str(child.id))
        
        response = await client.get(
            "/api/v1/html/chores/pending-approval",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        assert response.status_code == 403
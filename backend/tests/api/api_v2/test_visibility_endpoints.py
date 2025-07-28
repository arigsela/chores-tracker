"""Tests for V2 visibility management endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.models.chore_visibility import ChoreVisibility
from backend.app.core.security.password import get_password_hash


@pytest.fixture
async def parent_user_with_token(db_session: AsyncSession, client: AsyncClient):
    """Create a parent user and get auth token."""
    # Create parent user
    parent = User(
        username="parent_visibility@test.com",
        email="parent_visibility@test.com",
        hashed_password=get_password_hash("password123"),
        is_parent=True
    )
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)
    
    # Login to get token
    response = await client.post(
        "/api/v1/users/login",
        data={"username": "parent_visibility@test.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    
    return parent, token


@pytest.fixture
async def child_users(db_session: AsyncSession, parent_user_with_token):
    """Create child users."""
    parent, _ = parent_user_with_token
    
    child1 = User(
        username="child1_visibility@test.com",
        email="child1_visibility@test.com",
        hashed_password="hashed",
        is_parent=False,
        parent_id=parent.id
    )
    child2 = User(
        username="child2_visibility@test.com",
        email="child2_visibility@test.com",
        hashed_password="hashed",
        is_parent=False,
        parent_id=parent.id
    )
    
    db_session.add_all([child1, child2])
    await db_session.commit()
    await db_session.refresh(child1)
    await db_session.refresh(child2)
    
    return child1, child2


@pytest.fixture
async def test_chore(db_session: AsyncSession, parent_user_with_token):
    """Create a test chore."""
    parent, _ = parent_user_with_token
    
    chore = Chore(
        title="Test Visibility Chore",
        description="A chore for testing visibility",
        reward=5.0,
        creator_id=parent.id,
        assignee_id=None  # Pool chore
    )
    db_session.add(chore)
    await db_session.commit()
    await db_session.refresh(chore)
    
    return chore


class TestVisibilityEndpoints:
    """Test cases for visibility management endpoints."""
    
    async def test_update_visibility_as_parent(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        parent_user_with_token,
        child_users,
        test_chore
    ):
        """Test parent can update visibility settings."""
        parent, token = parent_user_with_token
        child1, child2 = child_users
        
        # Update visibility - hide from child1, show to child2
        response = await client.put(
            f"/api/v2/chores/{test_chore.id}/visibility",
            json={
                "chore_id": test_chore.id,
                "hidden_from_users": [child1.id],
                "visible_to_users": [child2.id]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify visibility settings
        for record in data:
            if record["user_id"] == child1.id:
                assert record["is_hidden"] is True
            elif record["user_id"] == child2.id:
                assert record["is_hidden"] is False
    
    async def test_update_visibility_as_child_forbidden(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        parent_user_with_token,
        child_users,
        test_chore
    ):
        """Test child cannot update visibility."""
        parent, _ = parent_user_with_token
        child1, child2 = child_users
        
        # Create child token
        child1.hashed_password = get_password_hash("password123")
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/users/login",
            data={"username": "child1_visibility@test.com", "password": "password123"}
        )
        child_token = response.json()["access_token"]
        
        # Try to update visibility as child
        response = await client.put(
            f"/api/v2/chores/{test_chore.id}/visibility",
            json={
                "chore_id": test_chore.id,
                "hidden_from_users": [child2.id]
            },
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        assert response.status_code == 403
        assert "Only parents can manage" in response.json()["detail"]
    
    async def test_get_visibility_returns_current_settings(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        parent_user_with_token,
        child_users,
        test_chore
    ):
        """Test retrieving current visibility settings."""
        parent, token = parent_user_with_token
        child1, child2 = child_users
        
        # Set some visibility
        visibility = ChoreVisibility(
            chore_id=test_chore.id,
            user_id=child1.id,
            is_hidden=True
        )
        db_session.add(visibility)
        await db_session.commit()
        
        # Get visibility settings
        response = await client.get(
            f"/api/v2/chores/{test_chore.id}/visibility",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == child1.id
        assert data[0]["is_hidden"] is True
    
    async def test_update_visibility_for_specific_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        parent_user_with_token,
        child_users,
        test_chore
    ):
        """Test updating visibility for a specific user."""
        parent, token = parent_user_with_token
        child1, _ = child_users
        
        # Update visibility for child1
        response = await client.put(
            f"/api/v2/chores/{test_chore.id}/visibility/user/{child1.id}",
            json={"is_hidden": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == child1.id
        assert data["is_hidden"] is True
        assert data["chore_id"] == test_chore.id
    
    async def test_update_visibility_wrong_parent(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        parent_user_with_token,
        test_chore
    ):
        """Test parent cannot update visibility for another parent's chore."""
        # Create another parent
        other_parent = User(
            username="other_parent@test.com",
            email="other_parent@test.com",
            hashed_password=get_password_hash("password123"),
            is_parent=True
        )
        db_session.add(other_parent)
        await db_session.commit()
        
        # Login as other parent
        response = await client.post(
            "/api/v1/users/login",
            data={"username": "other_parent@test.com", "password": "password123"}
        )
        other_token = response.json()["access_token"]
        
        # Try to update visibility
        response = await client.put(
            f"/api/v2/chores/{test_chore.id}/visibility",
            json={
                "chore_id": test_chore.id,
                "hidden_from_users": [1]
            },
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 403
        assert "only manage visibility for chores you created" in response.json()["detail"]
    
    async def test_visibility_nonexistent_chore(
        self,
        client: AsyncClient,
        parent_user_with_token
    ):
        """Test visibility operations on non-existent chore."""
        _, token = parent_user_with_token
        
        # Try to update visibility for non-existent chore
        response = await client.put(
            "/api/v2/chores/99999/visibility",
            json={
                "chore_id": 99999,
                "hidden_from_users": [1]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
        assert "Chore not found" in response.json()["detail"]
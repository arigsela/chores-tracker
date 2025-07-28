"""Tests for V2 enhanced chore endpoints."""
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.models.chore import Chore, RecurrenceType
from backend.app.models.chore_visibility import ChoreVisibility
from backend.app.core.security.password import get_password_hash


@pytest.fixture
async def parent_and_children_with_tokens(db_session: AsyncSession, client: AsyncClient):
    """Create a parent with two children and get auth tokens."""
    # Create parent
    parent = User(
        username="parent_pool@test.com",
        email="parent_pool@test.com",
        hashed_password=get_password_hash("password123"),
        is_parent=True
    )
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)
    
    # Create children
    child1 = User(
        username="child1_pool@test.com",
        email="child1_pool@test.com",
        hashed_password=get_password_hash("password123"),
        is_parent=False,
        parent_id=parent.id
    )
    child2 = User(
        username="child2_pool@test.com",
        email="child2_pool@test.com",
        hashed_password=get_password_hash("password123"),
        is_parent=False,
        parent_id=parent.id
    )
    db_session.add_all([child1, child2])
    await db_session.commit()
    await db_session.refresh(child1)
    await db_session.refresh(child2)
    
    # Get tokens
    parent_response = await client.post(
        "/api/v1/users/login",
        data={"username": "parent_pool@test.com", "password": "password123"}
    )
    parent_token = parent_response.json()["access_token"]
    
    child1_response = await client.post(
        "/api/v1/users/login",
        data={"username": "child1_pool@test.com", "password": "password123"}
    )
    child1_token = child1_response.json()["access_token"]
    
    child2_response = await client.post(
        "/api/v1/users/login",
        data={"username": "child2_pool@test.com", "password": "password123"}
    )
    child2_token = child2_response.json()["access_token"]
    
    return {
        "parent": parent,
        "parent_token": parent_token,
        "child1": child1,
        "child1_token": child1_token,
        "child2": child2,
        "child2_token": child2_token
    }


@pytest.fixture
async def pool_chores(db_session: AsyncSession, parent_and_children_with_tokens):
    """Create pool chores with various states."""
    data = parent_and_children_with_tokens
    parent = data["parent"]
    child1 = data["child1"]
    
    # Available pool chore
    available_chore = Chore(
        title="Available Pool Chore",
        description="Can be claimed",
        reward=5.0,
        creator_id=parent.id,
        assignee_id=None,
        recurrence_type=RecurrenceType.NONE
    )
    
    # Recurring chore that was completed recently (not available)
    completed_recurring = Chore(
        title="Daily Chore",
        description="Completed today",
        reward=3.0,
        creator_id=parent.id,
        assignee_id=None,
        recurrence_type=RecurrenceType.DAILY,
        last_completion_time=datetime.now(timezone.utc) - timedelta(hours=6)
    )
    
    # Hidden chore
    hidden_chore = Chore(
        title="Hidden Chore",
        description="Hidden from child1",
        reward=10.0,
        creator_id=parent.id,
        assignee_id=None,
        recurrence_type=RecurrenceType.NONE
    )
    
    db_session.add_all([available_chore, completed_recurring, hidden_chore])
    await db_session.commit()
    
    # Hide chore from child1
    visibility = ChoreVisibility(
        chore_id=hidden_chore.id,
        user_id=child1.id,
        is_hidden=True
    )
    db_session.add(visibility)
    await db_session.commit()
    
    await db_session.refresh(available_chore)
    await db_session.refresh(completed_recurring)
    await db_session.refresh(hidden_chore)
    
    return {
        "available": available_chore,
        "completed_recurring": completed_recurring,
        "hidden": hidden_chore
    }


class TestChoreEndpointsV2:
    """Test cases for V2 chore endpoints."""
    
    async def test_get_pool_chores_as_child(
        self,
        client: AsyncClient,
        parent_and_children_with_tokens,
        pool_chores
    ):
        """Test child sees filtered pool chores."""
        data = parent_and_children_with_tokens
        child1_token = data["child1_token"]
        chores = pool_chores
        
        response = await client.get(
            "/api/v2/chores/pool",
            headers={"Authorization": f"Bearer {child1_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should have available and completed lists
        assert "available_chores" in result
        assert "completed_chores" in result
        
        # Available should have only the available chore (hidden is filtered out)
        assert len(result["available_chores"]) == 1
        assert result["available_chores"][0]["title"] == "Available Pool Chore"
        assert result["available_chores"][0]["is_available"] is True
        assert result["available_chores"][0]["availability_progress"] == 100
        
        # Completed should have the recurring chore
        assert len(result["completed_chores"]) == 1
        assert result["completed_chores"][0]["title"] == "Daily Chore"
        assert result["completed_chores"][0]["is_available"] is False
        assert 0 < result["completed_chores"][0]["availability_progress"] < 100
    
    async def test_get_pool_chores_as_parent(
        self,
        client: AsyncClient,
        parent_and_children_with_tokens,
        pool_chores
    ):
        """Test parent sees all pool chores."""
        data = parent_and_children_with_tokens
        parent_token = data["parent_token"]
        
        response = await client.get(
            "/api/v2/chores/pool",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Parent should see all chores (no filtering)
        total_chores = len(result["available_chores"]) + len(result["completed_chores"])
        assert total_chores == 3
    
    async def test_create_chore_with_visibility(
        self,
        client: AsyncClient,
        parent_and_children_with_tokens
    ):
        """Test creating chore with visibility settings."""
        data = parent_and_children_with_tokens
        parent_token = data["parent_token"]
        child1 = data["child1"]
        child2 = data["child2"]
        
        response = await client.post(
            "/api/v2/chores/",
            json={
                "title": "New Pool Chore",
                "description": "Hidden from child1",
                "reward": 7.5,
                "assignee_id": None,
                "hidden_from_users": [child1.id],
                "recurrence_type": "weekly",
                "recurrence_value": 1  # Monday
            },
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        assert response.status_code == 201
        chore_data = response.json()
        assert chore_data["title"] == "New Pool Chore"
        assert chore_data["assignee_id"] is None
        assert chore_data["recurrence_type"] == "weekly"
    
    async def test_claim_chore_success(
        self,
        client: AsyncClient,
        parent_and_children_with_tokens,
        pool_chores
    ):
        """Test successfully claiming a chore."""
        data = parent_and_children_with_tokens
        child1_token = data["child1_token"]
        child1 = data["child1"]
        available_chore = pool_chores["available"]
        
        response = await client.post(
            f"/api/v2/chores/{available_chore.id}/claim",
            headers={"Authorization": f"Bearer {child1_token}"}
        )
        
        assert response.status_code == 200
        chore_data = response.json()
        assert chore_data["assignee_id"] == child1.id
        assert chore_data["title"] == "Available Pool Chore"
    
    async def test_claim_hidden_chore_fails(
        self,
        client: AsyncClient,
        parent_and_children_with_tokens,
        pool_chores
    ):
        """Test claiming a hidden chore fails."""
        data = parent_and_children_with_tokens
        child1_token = data["child1_token"]
        hidden_chore = pool_chores["hidden"]
        
        response = await client.post(
            f"/api/v2/chores/{hidden_chore.id}/claim",
            headers={"Authorization": f"Bearer {child1_token}"}
        )
        
        assert response.status_code == 403
        assert "cannot claim this chore" in response.json()["detail"]
    
    async def test_claim_unavailable_chore_fails(
        self,
        client: AsyncClient,
        parent_and_children_with_tokens,
        pool_chores
    ):
        """Test claiming a chore in cooldown fails."""
        data = parent_and_children_with_tokens
        child1_token = data["child1_token"]
        completed_chore = pool_chores["completed_recurring"]
        
        response = await client.post(
            f"/api/v2/chores/{completed_chore.id}/claim",
            headers={"Authorization": f"Bearer {child1_token}"}
        )
        
        assert response.status_code == 400
        assert "not yet available" in response.json()["detail"]
    
    async def test_complete_pool_chore_auto_claims(
        self,
        client: AsyncClient,
        parent_and_children_with_tokens,
        pool_chores
    ):
        """Test completing unassigned chore auto-claims it."""
        data = parent_and_children_with_tokens
        child2_token = data["child2_token"]
        child2 = data["child2"]
        available_chore = pool_chores["available"]
        
        response = await client.post(
            f"/api/v2/chores/{available_chore.id}/complete",
            headers={"Authorization": f"Bearer {child2_token}"}
        )
        
        assert response.status_code == 200
        chore_data = response.json()
        assert chore_data["assignee_id"] == child2.id
        assert chore_data["is_completed"] is True
    
    async def test_get_chore_with_availability(
        self,
        client: AsyncClient,
        parent_and_children_with_tokens,
        pool_chores
    ):
        """Test getting single chore with availability info."""
        data = parent_and_children_with_tokens
        child1_token = data["child1_token"]
        completed_chore = pool_chores["completed_recurring"]
        
        response = await client.get(
            f"/api/v2/chores/{completed_chore.id}",
            headers={"Authorization": f"Bearer {child1_token}"}
        )
        
        assert response.status_code == 200
        chore_data = response.json()
        assert chore_data["title"] == "Daily Chore"
        assert chore_data["is_available"] is False
        assert "availability_progress" in chore_data
        assert 0 < chore_data["availability_progress"] < 100
        assert chore_data["is_hidden_from_current_user"] is False
    
    async def test_race_condition_claim(
        self,
        client: AsyncClient,
        parent_and_children_with_tokens,
        pool_chores
    ):
        """Test that only one child can claim a chore."""
        data = parent_and_children_with_tokens
        child1_token = data["child1_token"]
        child2_token = data["child2_token"]
        child1 = data["child1"]
        available_chore = pool_chores["available"]
        
        # Child1 claims first
        response1 = await client.post(
            f"/api/v2/chores/{available_chore.id}/claim",
            headers={"Authorization": f"Bearer {child1_token}"}
        )
        assert response1.status_code == 200
        
        # Child2 tries to claim same chore
        response2 = await client.post(
            f"/api/v2/chores/{available_chore.id}/claim",
            headers={"Authorization": f"Bearer {child2_token}"}
        )
        assert response2.status_code == 400
        assert "already assigned" in response2.json()["detail"]
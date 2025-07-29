"""Tests for v2 chore endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.chore import Chore


@pytest.mark.asyncio
async def test_create_chore_v2(
    async_client: AsyncClient,
    test_db: AsyncSession,
    test_parent_user: User,
    test_child_user: User,
    parent_headers: dict
):
    """Test creating chore with v2 endpoint."""
    response = await async_client.post(
        "/api/v2/chores/",
        json={
            "title": "Test Chore v2",
            "description": "Test description",
            "assignee_id": test_child_user.id,
            "reward": 10.0,
            "is_range_reward": False,
            "cooldown_days": 0,
            "recurrence_type": "none"
        },
        headers=parent_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["title"] == "Test Chore v2"
    assert data["data"]["assignee_id"] == test_child_user.id
    assert data["data"]["reward"] == 10.0


@pytest.mark.asyncio
async def test_list_chores_v2(
    async_client: AsyncClient,
    test_chore: Chore,
    parent_headers: dict
):
    """Test listing chores with v2 endpoint."""
    response = await async_client.get(
        "/api/v2/chores/",
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check paginated response
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert data["total"] >= 1
    assert data["page"] == 1
    assert data["page_size"] == 10


@pytest.mark.asyncio
async def test_get_chore_v2(
    async_client: AsyncClient,
    test_chore: Chore,
    parent_headers: dict
):
    """Test getting specific chore with v2 endpoint."""
    response = await async_client.get(
        f"/api/v2/chores/{test_chore.id}",
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["id"] == test_chore.id
    assert data["data"]["title"] == test_chore.title


@pytest.mark.asyncio
async def test_update_chore_v2(
    async_client: AsyncClient,
    test_chore: Chore,
    parent_headers: dict
):
    """Test updating chore with v2 endpoint."""
    response = await async_client.put(
        f"/api/v2/chores/{test_chore.id}",
        json={"description": "Updated description"},
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["description"] == "Updated description"


@pytest.mark.asyncio
async def test_complete_chore_v2(
    async_client: AsyncClient,
    test_chore: Chore,
    child_headers: dict
):
    """Test completing chore with v2 endpoint."""
    response = await async_client.post(
        f"/api/v2/chores/{test_chore.id}/complete",
        headers=child_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["is_completed"] is True
    assert data["data"]["completion_date"] is not None


@pytest.mark.asyncio
async def test_approve_chore_v2(
    async_client: AsyncClient,
    test_db: AsyncSession,
    test_parent_user: User,
    test_child_user: User,
    parent_headers: dict,
    child_headers: dict
):
    """Test approving chore with v2 endpoint."""
    # Create and complete a chore
    create_response = await async_client.post(
        "/api/v2/chores/",
        json={
            "title": "Chore to approve",
            "description": "Test",
            "assignee_id": test_child_user.id,
            "reward": 5.0,
            "is_range_reward": False,
            "cooldown_days": 0,
            "recurrence_type": "none"
        },
        headers=parent_headers
    )
    chore_id = create_response.json()["data"]["id"]
    
    # Complete it
    await async_client.post(
        f"/api/v2/chores/{chore_id}/complete",
        headers=child_headers
    )
    
    # Approve it
    response = await async_client.post(
        f"/api/v2/chores/{chore_id}/approve",
        json={"reward_value": 5.0},
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["is_approved"] is True
    assert data["data"]["approved_reward"] == 5.0


@pytest.mark.asyncio
async def test_disable_chore_v2(
    async_client: AsyncClient,
    test_chore: Chore,
    parent_headers: dict
):
    """Test disabling chore with v2 endpoint."""
    response = await async_client.post(
        f"/api/v2/chores/{test_chore.id}/disable",
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["is_disabled"] is True


@pytest.mark.asyncio
async def test_chore_stats_v2(
    async_client: AsyncClient,
    test_chore: Chore,
    parent_headers: dict
):
    """Test getting chore statistics with v2 endpoint."""
    response = await async_client.get(
        "/api/v2/chores/stats/summary",
        headers=parent_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "total_chores" in data["data"]
    assert "completed_chores" in data["data"]
    assert "approved_chores" in data["data"]
    assert "total_earned" in data["data"]
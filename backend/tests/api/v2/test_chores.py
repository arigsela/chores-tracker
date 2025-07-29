"""Tests for v2 chore endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_chore_v2(
    client: AsyncClient,
    test_parent_user,
    test_child_user,
    parent_token
):
    """Test creating chore with v2 endpoint."""
    response = await client.post(
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
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["title"] == "Test Chore v2"
    assert data["data"]["assignee_id"] == test_child_user.id
    assert data["data"]["reward"] == 10.0


@pytest.mark.asyncio
async def test_list_chores_v2(
    client: AsyncClient,
    test_chore,
    parent_token
):
    """Test listing chores with v2 endpoint."""
    response = await client.get(
        "/api/v2/chores/",
        headers={"Authorization": f"Bearer {parent_token}"}
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
    client: AsyncClient,
    test_chore,
    parent_token
):
    """Test getting specific chore with v2 endpoint."""
    response = await client.get(
        f"/api/v2/chores/{test_chore.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["id"] == test_chore.id
    assert data["data"]["title"] == test_chore.title


@pytest.mark.asyncio
async def test_update_chore_v2(
    client: AsyncClient,
    test_parent_user,
    test_child_user,
    parent_token
):
    """Test updating chore with v2 endpoint."""
    # Create a fresh chore for this test
    create_response = await client.post(
        "/api/v2/chores/",
        json={
            "title": "Chore to update v2",
            "description": "Original description",
            "assignee_id": test_child_user.id,
            "reward": 7.0,
            "is_range_reward": False,
            "cooldown_days": 0,
            "recurrence_type": "none"
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    chore_id = create_response.json()["data"]["id"]
    
    # Update it
    response = await client.put(
        f"/api/v2/chores/{chore_id}",
        json={"description": "Updated description v2"},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["description"] == "Updated description v2"


@pytest.mark.asyncio
async def test_complete_chore_v2(
    client: AsyncClient,
    test_parent_user,
    test_child_user,
    parent_token,
    child_token
):
    """Test completing chore with v2 endpoint."""
    # Create a fresh chore for this test
    create_response = await client.post(
        "/api/v2/chores/",
        json={
            "title": "Chore to complete v2",
            "description": "Test",
            "assignee_id": test_child_user.id,
            "reward": 3.0,
            "is_range_reward": False,
            "cooldown_days": 0,
            "recurrence_type": "none"
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    chore_id = create_response.json()["data"]["id"]
    
    # Now complete it
    response = await client.post(
        f"/api/v2/chores/{chore_id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["is_completed"] is True
    assert data["data"]["completion_date"] is not None


@pytest.mark.asyncio
async def test_approve_chore_v2(
    client: AsyncClient,
    test_parent_user,
    test_child_user,
    parent_token,
    child_token
):
    """Test approving chore with v2 endpoint."""
    # Create and complete a chore
    create_response = await client.post(
        "/api/v2/chores/",
        json={
            "title": "Chore to approve v2",
            "description": "Test",
            "assignee_id": test_child_user.id,
            "reward": 5.0,
            "is_range_reward": False,
            "cooldown_days": 0,
            "recurrence_type": "none"
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    chore_id = create_response.json()["data"]["id"]
    
    # Complete it
    await client.post(
        f"/api/v2/chores/{chore_id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    
    # Approve it
    response = await client.post(
        f"/api/v2/chores/{chore_id}/approve",
        json={"reward_value": 5.0},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["is_approved"] is True
    assert data["data"]["reward"] == 5.0


@pytest.mark.asyncio
async def test_disable_chore_v2(
    client: AsyncClient,
    test_parent_user,
    test_child_user,
    parent_token
):
    """Test disabling chore with v2 endpoint."""
    # Create a fresh chore for this test
    create_response = await client.post(
        "/api/v2/chores/",
        json={
            "title": "Chore to disable v2",
            "description": "Test",
            "assignee_id": test_child_user.id,
            "reward": 2.0,
            "is_range_reward": False,
            "cooldown_days": 0,
            "recurrence_type": "none"
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    chore_id = create_response.json()["data"]["id"]
    
    # Disable it
    response = await client.post(
        f"/api/v2/chores/{chore_id}/disable",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["is_disabled"] is True


@pytest.mark.asyncio
async def test_chore_stats_v2(
    client: AsyncClient,
    test_chore,
    parent_token
):
    """Test getting chore statistics with v2 endpoint."""
    response = await client.get(
        "/api/v2/chores/stats/summary",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "total_chores" in data["data"]
    assert "completed_chores" in data["data"]
    assert "approved_chores" in data["data"]
    assert "total_earned" in data["data"]
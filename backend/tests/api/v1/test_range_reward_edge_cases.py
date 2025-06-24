import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.chore import Chore

@pytest.mark.asyncio
async def test_approve_range_reward_below_minimum(
    client: AsyncClient,
    parent_token,
    child_token,
    test_range_chore,
    db_session: AsyncSession
):
    """Test approving a range reward chore with a value below the minimum."""
    # Complete the chore first
    response = await client.post(
        f"/api/v1/chores/{test_range_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    
    # Try to approve with a value below the minimum
    min_reward = test_range_chore.min_reward
    below_min = min_reward - 0.50
    
    response = await client.post(
        f"/api/v1/chores/{test_range_chore.id}/approve",
        json={"reward_value": below_min},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    # The API should either reject this or cap it at the minimum
    if response.status_code == 422:
        # If it rejects with validation error
        error_message = response.json()["detail"]
        assert "minimum" in error_message.lower() or str(min_reward) in error_message
    elif response.status_code == 400:
        # If it rejects with bad request
        error_detail = response.json()["detail"]
        # Handle both string and list error messages
        if isinstance(error_detail, list):
            error_message = " ".join([str(err).lower() for err in error_detail])
        else:
            error_message = error_detail.lower()
        # Check for the specific error message format
        assert "between" in error_message or str(min_reward).lower() in error_message
    else:
        # If it allows but caps the value, check that the value was capped
        assert response.status_code == 200
        data = response.json()
        assert data["reward"] >= min_reward

@pytest.mark.asyncio
async def test_approve_range_reward_above_maximum(
    client: AsyncClient,
    parent_token,
    child_token,
    test_range_chore,
    db_session: AsyncSession
):
    """Test approving a range reward chore with a value above the maximum."""
    # Complete the chore first
    response = await client.post(
        f"/api/v1/chores/{test_range_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    
    # Try to approve with a value above the maximum
    max_reward = test_range_chore.max_reward
    above_max = max_reward + 1.00
    
    response = await client.post(
        f"/api/v1/chores/{test_range_chore.id}/approve",
        json={"reward_value": above_max},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    # The API should either reject this or cap it at the maximum
    if response.status_code == 422:
        # If it rejects with validation error
        error_message = response.json()["detail"]
        assert "maximum" in error_message.lower() or str(max_reward) in error_message
    elif response.status_code == 400:
        # If it rejects with bad request
        error_message = response.json()["detail"].lower()
        # Check for the specific error message format
        assert "between" in error_message or str(max_reward).lower() in error_message
    else:
        # If it allows but caps the value, check that the value was capped
        assert response.status_code == 200
        data = response.json()
        assert data["reward"] <= max_reward

@pytest.mark.asyncio
async def test_approve_range_reward_with_negative_value(
    client: AsyncClient,
    parent_token,
    child_token,
    test_range_chore,
    db_session: AsyncSession
):
    """Test approving a range reward chore with a negative value."""
    # Complete the chore first
    response = await client.post(
        f"/api/v1/chores/{test_range_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    
    # Try to approve with a negative value
    response = await client.post(
        f"/api/v1/chores/{test_range_chore.id}/approve",
        json={"reward_value": -1.00},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    # The API should reject this (rewards should not be negative)
    assert response.status_code in [400, 422]
    error_detail = response.json()["detail"]
    
    # Handle both string and list error messages
    if isinstance(error_detail, list):
        # For validation errors, check all error messages
        error_messages = [str(err).lower() for err in error_detail]
        error_message = " ".join(error_messages)
    else:
        error_message = error_detail.lower()
    
    assert "negative" in error_message or "invalid" in error_message or "value" in error_message or "greater" in error_message

@pytest.mark.asyncio
async def test_zero_reward_for_range_chore(
    client: AsyncClient,
    parent_token,
    child_token,
    db_session: AsyncSession
):
    """Test creating and approving a range reward chore with zero rewards."""
    # Create a range reward chore with zero min/max
    response = await client.post(
        "/api/v1/chores/",
        json={
            "title": "Zero reward chore",
            "description": "Min/max reward set to zero",
            "is_range_reward": True,
            "min_reward": 0.0,
            "max_reward": 0.0,
            "assignee_id": 2  # Assuming child ID is 2
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 201
    chore_id = response.json()["id"]
    
    # Complete the chore
    response = await client.post(
        f"/api/v1/chores/{chore_id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    
    # Approve with zero reward
    response = await client.post(
        f"/api/v1/chores/{chore_id}/approve",
        json={"reward_value": 0.0},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reward"] == 0.0
    assert data["is_approved"] is True 
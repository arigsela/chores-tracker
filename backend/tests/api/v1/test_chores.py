import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

from backend.app.models.chore import Chore
from backend.app.models.chore_assignment import ChoreAssignment


@pytest.mark.asyncio
async def test_create_chore(client: AsyncClient, parent_token, test_child_user):
    """Test creating a chore with fixed reward."""
    # Test creating a chore as a parent
    response = await client.post(
        "/api/v1/chores",
        json={
            "title": "Take out the trash",
            "description": "Empty all trash cans and take to the curb",
            "reward": 2.5,
            "is_range_reward": False,
            "cooldown_days": 7,
            "is_recurring": True,
            "frequency": "weekly",
            "assignment_mode": "single",
            "assignee_ids": [test_child_user.id]
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Take out the trash"
    assert data["description"] == "Empty all trash cans and take to the curb"
    assert data["reward"] == 2.5
    assert data["is_range_reward"] == False
    assert data["cooldown_days"] == 7
    assert data["is_recurring"] == True
    assert data["frequency"] == "weekly"
    assert data["assignment_mode"] == "single"
    assert data["is_disabled"] == False
    # Verify assignment was created in the assignments relationship
    assert len(data["assignments"]) == 1
    assert data["assignments"][0]["assignee_id"] == test_child_user.id
    assert data["assignments"][0]["is_completed"] == False
    assert data["assignments"][0]["is_approved"] == False


@pytest.mark.asyncio
async def test_create_range_reward_chore(client: AsyncClient, parent_token, test_child_user):
    """Test creating a chore with range-based reward."""
    response = await client.post(
        "/api/v1/chores",
        json={
            "title": "Wash dishes",
            "description": "Wash all dirty dishes in the sink",
            "is_range_reward": True,
            "min_reward": 1.5,
            "max_reward": 3.0,
            "cooldown_days": 1,
            "assignment_mode": "single",
            "assignee_ids": [test_child_user.id]
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Wash dishes"
    assert data["is_range_reward"] == True
    assert data["min_reward"] == 1.5
    assert data["max_reward"] == 3.0
    assert data["cooldown_days"] == 1
    assert data["assignment_mode"] == "single"
    # Verify assignment was created
    assert len(data["assignments"]) == 1
    assert data["assignments"][0]["assignee_id"] == test_child_user.id


@pytest.mark.asyncio
async def test_create_range_reward_chore_with_empty_reward(client: AsyncClient, parent_token, test_child_user):
    """Test creating a range reward chore with an empty reward field."""
    # Create chore with form data similar to the issue reported
    response = await client.post(
        "/api/v1/chores",
        data={
            "title": "Take a shower",
            "description": "",
            "is_range_reward": "on",
            "reward": "",  # Empty reward
            "min_reward": "1",
            "max_reward": "2",
            "cooldown_days": "1",
            "assignee_id": str(test_child_user.id),  # Form data uses assignee_id
            "frequency": "daily"
        },
        headers={
            "Authorization": f"Bearer {parent_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    assert response.status_code == 201, f"Response: {response.text}"
    data = response.json()
    assert data["title"] == "Take a shower"
    assert data["is_range_reward"] == True
    assert data["min_reward"] == 1.0
    assert data["max_reward"] == 2.0
    assert data["cooldown_days"] == 1
    assert data["assignment_mode"] == "single"
    # Verify assignment was created
    assert len(data["assignments"]) == 1
    assert data["assignments"][0]["assignee_id"] == test_child_user.id


@pytest.mark.asyncio
async def test_child_cannot_create_chore(client: AsyncClient, child_token, test_parent_user):
    """Test that a child cannot create a chore."""
    response = await client.post(
        "/api/v1/chores",
        json={
            "title": "Clean my room",
            "description": "Tidy up my room",
            "reward": 1.0,
            "assignment_mode": "single",
            "assignee_ids": [test_parent_user.id]
        },
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only parents can create chores" in response.json()["detail"]


@pytest.mark.asyncio
async def test_read_chores(client: AsyncClient, parent_token, child_token, test_chore, test_range_chore, test_disabled_chore):
    """Test reading chores."""
    # Parent should see all active (non-disabled) chores they created
    response = await client.get(
        "/api/v1/chores",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Only non-disabled chores
    titles = [chore["title"] for chore in data]
    assert "Clean room" in titles
    assert "Take out trash" in titles
    # "Mow lawn" is disabled and should not appear

    # Child should see only non-disabled chores assigned to them
    response = await client.get(
        "/api/v1/chores",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = [chore["title"] for chore in data]
    assert "Clean room" in titles
    assert "Take out trash" in titles
    assert "Mow lawn" not in titles  # This is disabled


@pytest.mark.asyncio
async def test_read_available_chores(client: AsyncClient, child_token, test_chore, test_range_chore):
    """Test reading available chores for a child."""
    response = await client.get(
        "/api/v1/chores/available",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    # The /available endpoint returns {assigned: [...], pool: [...]}
    # Each item in assigned has structure: {"chore": {...}, "assignment": {...}, "assignment_id": ...}
    assert "assigned" in data
    assert "pool" in data
    assert len(data["assigned"]) == 2
    titles = [item["chore"]["title"] for item in data["assigned"]]
    assert "Clean room" in titles
    assert "Take out trash" in titles


@pytest.mark.asyncio
async def test_read_pending_approval_chores(client: AsyncClient, parent_token, child_token, test_chore, test_range_chore):
    """Test reading chores pending approval."""
    # No chores pending approval initially
    response = await client.get(
        "/api/v1/chores/pending-approval",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    # Child completes chores
    await client.post(
        f"/api/v1/chores/{test_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    await client.post(
        f"/api/v1/chores/{test_range_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )

    # Now parent should see two assignments pending approval
    response = await client.get(
        "/api/v1/chores/pending-approval",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    # The response is now assignment-level data
    assert len(data) == 2
    # Each item has assignment details and chore info
    for item in data:
        assert "assignment" in item
        assert "chore" in item
        assert item["assignment"]["is_completed"] == True
        assert item["assignment"]["is_approved"] == False

    chore_titles = [item["chore"]["title"] for item in data]
    assert "Clean room" in chore_titles
    assert "Take out trash" in chore_titles

    # Child cannot access the pending-approval endpoint
    response = await client.get(
        "/api/v1/chores/pending-approval",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "This endpoint is only for parent users" in response.json()["detail"]


@pytest.mark.asyncio
async def test_read_chore_by_id(client: AsyncClient, parent_token, child_token, test_chore):
    """Test reading a specific chore."""
    # Parent can access the chore
    response = await client.get(
        f"/api/v1/chores/{test_chore.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Clean room"
    assert data["is_range_reward"] == False
    assert data["reward"] == 5.00
    assert data["assignment_mode"] == "single"

    # Child can access the chore
    response = await client.get(
        f"/api/v1/chores/{test_chore.id}",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Clean room"


@pytest.mark.asyncio
async def test_read_range_chore_by_id(client: AsyncClient, parent_token, test_range_chore):
    """Test reading a range-based reward chore."""
    response = await client.get(
        f"/api/v1/chores/{test_range_chore.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Take out trash"
    assert data["is_range_reward"] == True
    assert data["min_reward"] == 2.00
    assert data["max_reward"] == 4.00
    assert data["cooldown_days"] == 7
    assert data["assignment_mode"] == "single"


@pytest.mark.asyncio
async def test_update_chore(client: AsyncClient, parent_token, child_token, test_chore):
    """Test updating a chore."""
    # Parent can update the chore
    response = await client.put(
        f"/api/v1/chores/{test_chore.id}",
        json={
            "title": "Clean room thoroughly",
            "reward": 7.50,
            "cooldown_days": 3
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Clean room thoroughly"
    assert data["reward"] == 7.50
    assert data["cooldown_days"] == 3

    # Child cannot update the chore
    response = await client.put(
        f"/api/v1/chores/{test_chore.id}",
        json={
            "title": "Just tidying up a bit",
            "reward": 10.00
        },
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only parents can update chores" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_chore_to_range_reward(client: AsyncClient, parent_token, test_chore):
    """Test converting a fixed reward chore to range-based reward."""
    response = await client.put(
        f"/api/v1/chores/{test_chore.id}",
        json={
            "is_range_reward": True,
            "min_reward": 3.50,
            "max_reward": 8.00
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_range_reward"] == True
    assert data["min_reward"] == 3.50
    assert data["max_reward"] == 8.00


@pytest.mark.asyncio
async def test_complete_and_approve_fixed_reward_chore(client: AsyncClient, parent_token, child_token, test_chore):
    """Test completing and approving a fixed reward chore."""
    # Child completes the chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    # Response now includes assignment data
    assert "assignment" in data
    assert "chore" in data
    assert data["assignment"]["is_completed"] == True
    assert data["assignment"]["is_approved"] == False
    assert data["assignment"]["completion_date"] is not None

    assignment_id = data["assignment"]["id"]

    # Child cannot approve their own chore
    response = await client.post(
        f"/api/v1/assignments/{assignment_id}/approve",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only parents can approve assignments" in response.json()["detail"]

    # Parent approves the assignment using the assignment endpoint
    response = await client.post(
        f"/api/v1/assignments/{assignment_id}/approve",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "assignment" in data
    assert data["assignment"]["is_completed"] == True
    assert data["assignment"]["is_approved"] == True
    assert data["assignment"]["approval_reward"] == 5.00  # Fixed reward


@pytest.mark.asyncio
async def test_complete_and_approve_range_reward_chore(client: AsyncClient, parent_token, child_token, test_range_chore):
    """Test completing and approving a range reward chore with custom value."""
    # Child completes the chore
    response = await client.post(
        f"/api/v1/chores/{test_range_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "assignment" in data
    assert data["assignment"]["is_completed"] == True
    assert data["assignment"]["is_approved"] == False

    assignment_id = data["assignment"]["id"]

    # Parent approves the assignment with a custom reward
    reward_value = 3.50  # Within min-max range
    response = await client.post(
        f"/api/v1/assignments/{assignment_id}/approve",
        json={"reward_value": reward_value},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "assignment" in data
    assert data["assignment"]["is_completed"] == True
    assert data["assignment"]["is_approved"] == True
    assert data["assignment"]["approval_reward"] == reward_value  # Set to the provided value


@pytest.mark.asyncio
async def test_approve_range_reward_outside_bounds(client: AsyncClient, parent_token, child_token, test_range_chore):
    """Test that approving with a reward outside the range is rejected."""
    # Child completes the chore
    response = await client.post(
        f"/api/v1/chores/{test_range_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    assignment_id = response.json()["assignment"]["id"]

    # Try to approve with a value below minimum
    response = await client.post(
        f"/api/v1/assignments/{assignment_id}/approve",
        json={"reward_value": 1.00},  # Below min_reward of 2.00
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 422
    assert "Reward value must be between" in response.json()["detail"]

    # Try to approve with a value above maximum
    response = await client.post(
        f"/api/v1/assignments/{assignment_id}/approve",
        json={"reward_value": 5.00},  # Above max_reward of 4.00
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 422
    assert "Reward value must be between" in response.json()["detail"]


@pytest.mark.asyncio
async def test_approve_already_approved_chore(client: AsyncClient, parent_token, child_token, test_chore):
    """Test that approving an already approved assignment fails."""
    # Child completes the chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assignment_id = response.json()["assignment"]["id"]

    # Parent approves the assignment
    await client.post(
        f"/api/v1/assignments/{assignment_id}/approve",
        headers={"Authorization": f"Bearer {parent_token}"}
    )

    # Try to approve again
    response = await client.post(
        f"/api/v1/assignments/{assignment_id}/approve",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 400
    # The error message may reference "assignment" instead of "chore"
    detail = response.json()["detail"].lower()
    assert "already approved" in detail


@pytest.mark.asyncio
async def test_approve_uncompleted_chore(client: AsyncClient, parent_token, test_chore, db_session):
    """Test that approving an uncompleted assignment fails."""
    # Get the assignment ID from the test_chore fixture
    # The fixture creates an assignment, so we need to query it
    from sqlalchemy import select
    result = await db_session.execute(
        select(ChoreAssignment).where(ChoreAssignment.chore_id == test_chore.id)
    )
    assignment = result.scalar_one()

    response = await client.post(
        f"/api/v1/assignments/{assignment.id}/approve",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "must be completed" in detail or "not completed" in detail


@pytest.mark.asyncio
async def test_disable_chore(client: AsyncClient, parent_token, child_token, test_chore):
    """Test disabling a chore."""
    # Child cannot disable a chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/disable",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only parents can disable chores" in response.json()["detail"]

    # Parent can disable the chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/disable",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_disabled"] == True

    # Child can no longer complete the disabled chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 400
    assert "Cannot complete a disabled chore" in response.json()["detail"]


@pytest.mark.asyncio
async def test_enable_chore(client: AsyncClient, parent_token, child_token, test_chore, db_session):
    """Test enabling a disabled chore."""
    # First disable the chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/disable",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_disabled"] == True

    # Child cannot enable a chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/enable",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only parents can enable chores" in response.json()["detail"]

    # Parent can enable the chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/enable",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_disabled"] == False

    # Cannot enable an already enabled chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/enable",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 400
    assert "Chore is not disabled" in response.json()["detail"]

    # Child can now complete the enabled chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    assert "assignment" in response.json()
    assert response.json()["assignment"]["is_completed"] == True


@pytest.mark.asyncio
async def test_child_chores_endpoint(client: AsyncClient, parent_token, test_child_user, test_chore, test_range_chore):
    """Test the parent endpoint to view a specific child's chores."""
    response = await client.get(
        f"/api/v1/chores/child/{test_child_user.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = [chore["title"] for chore in data]
    assert "Clean room" in titles
    assert "Take out trash" in titles


@pytest.mark.asyncio
async def test_child_completed_chores_endpoint(client: AsyncClient, parent_token, child_token, test_child_user, test_chore):
    """Test the parent endpoint to view a specific child's completed chores."""
    # Child completes a chore
    await client.post(
        f"/api/v1/chores/{test_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )

    # Parent views the child's completed chores
    response = await client.get(
        f"/api/v1/chores/child/{test_child_user.id}/completed",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Clean room"
    # In multi-assignment, the chore itself doesn't have is_completed
    # but the response may include assignments
    assert data[0]["assignment_mode"] == "single"


@pytest.mark.asyncio
async def test_unauthorized_access_to_child_chores(client: AsyncClient, parent_token, child_token):
    """Test that a child cannot access the child-specific endpoints."""
    # Make up a random child ID
    child_id = 9999

    # Child user attempts to access child chores endpoint
    response = await client.get(
        f"/api/v1/chores/child/{child_id}",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only parents can view" in response.json()["detail"]

    # Child user attempts to access child completed chores endpoint
    response = await client.get(
        f"/api/v1/chores/child/{child_id}/completed",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only parents can view" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_chore(client: AsyncClient, parent_token, child_token, test_chore):
    """Test deleting a chore."""
    # Child cannot delete a chore
    response = await client.delete(
        f"/api/v1/chores/{test_chore.id}",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only parents can delete chores" in response.json()["detail"]

    # Parent can delete the chore
    response = await client.delete(
        f"/api/v1/chores/{test_chore.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 204

    # Verify the chore is gone
    response = await client.get(
        f"/api/v1/chores/{test_chore.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 404
    assert "Chore not found" in response.json()["detail"]

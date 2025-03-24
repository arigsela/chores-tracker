import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_chore(client: AsyncClient, parent_token, test_child_user):
    """Test creating a chore."""
    # Test creating a chore as a parent
    response = await client.post(
        "/api/v1/chores/",
        json={
            "title": "Take out the trash",
            "description": "Empty all trash cans and take to the curb",
            "reward": 2.5,
            "is_recurring": True,
            "frequency": "weekly",
            "assignee_id": test_child_user.id
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Take out the trash"
    assert data["description"] == "Empty all trash cans and take to the curb"
    assert data["reward"] == 2.5
    assert data["is_recurring"] == True
    assert data["frequency"] == "weekly"
    assert data["assignee_id"] == test_child_user.id
    assert data["is_completed"] == False
    assert data["is_approved"] == False


@pytest.mark.asyncio
async def test_child_cannot_create_chore(client: AsyncClient, child_token, test_parent_user):
    """Test that a child cannot create a chore."""
    response = await client.post(
        "/api/v1/chores/",
        json={
            "title": "Clean my room",
            "description": "Tidy up my room",
            "reward": 1.0,
            "assignee_id": test_parent_user.id
        },
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only parents can create chores" in response.json()["detail"]


@pytest.mark.asyncio
async def test_read_chores(client: AsyncClient, parent_token, child_token, test_chore):
    """Test reading chores."""
    # Parent should see the chore they created
    response = await client.get(
        "/api/v1/chores/",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Clean room"

    # Child should see the chore assigned to them
    response = await client.get(
        "/api/v1/chores/",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Clean room"


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

    # Child can access the chore
    response = await client.get(
        f"/api/v1/chores/{test_chore.id}",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Clean room"


@pytest.mark.asyncio
async def test_update_chore(client: AsyncClient, parent_token, child_token, test_chore):
    """Test updating a chore."""
    # Parent can update the chore
    response = await client.put(
        f"/api/v1/chores/{test_chore.id}",
        json={
            "title": "Clean room thoroughly",
            "reward": 7.50
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Clean room thoroughly"
    assert data["reward"] == 7.50

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
    assert "Not authorized to update this chore" in response.json()["detail"]


@pytest.mark.asyncio
async def test_complete_and_approve_chore(client: AsyncClient, parent_token, child_token, test_chore):
    """Test completing and approving a chore."""
    # Child completes the chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/complete",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] == True
    assert data["is_approved"] == False

    # Child cannot approve their own chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/approve",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Only the creator can approve chores" in response.json()["detail"]

    # Parent approves the chore
    response = await client.post(
        f"/api/v1/chores/{test_chore.id}/approve",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] == True
    assert data["is_approved"] == True


@pytest.mark.asyncio
async def test_delete_chore(client: AsyncClient, parent_token, child_token, test_chore):
    """Test deleting a chore."""
    # Child cannot delete a chore
    response = await client.delete(
        f"/api/v1/chores/{test_chore.id}",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    assert "Not authorized to delete this chore" in response.json()["detail"]

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
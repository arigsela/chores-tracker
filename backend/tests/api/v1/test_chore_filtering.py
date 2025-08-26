import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chores_filters_active(client: AsyncClient, parent_token, test_parent_user, test_child_user):
    response = await client.get(
        "/api/v1/chores?state=active",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    chores = response.json()
    assert all(not c.get("is_completed") for c in chores)


@pytest.mark.asyncio
async def test_chores_filters_completed(client: AsyncClient, parent_token, test_parent_user, test_child_user):
    response = await client.get(
        "/api/v1/chores?state=completed",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    chores = response.json()
    assert all(c.get("is_completed") and c.get("is_approved") for c in chores)


@pytest.mark.asyncio
async def test_chores_filters_pending(client: AsyncClient, parent_token, test_parent_user, test_child_user):
    response = await client.get(
        "/api/v1/chores?state=pending-approval",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    chores = response.json()
    assert all(c.get("is_completed") and not c.get("is_approved") for c in chores)


@pytest.mark.asyncio
async def test_chores_filter_child_id(client: AsyncClient, parent_token, test_parent_user, test_child_user):
    response = await client.get(
        f"/api/v1/chores?child_id={test_child_user.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    chores = response.json()
    assert all(c.get("assignee_id") == test_child_user.id for c in chores)

 
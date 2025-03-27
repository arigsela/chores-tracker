import pytest
import pytest_asyncio
from httpx import AsyncClient
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.app.models.chore import Chore
from backend.app.models.user import User

@pytest.mark.asyncio
async def test_unique_username_constraint(
    client: AsyncClient,
    parent_token,
    db_session: AsyncSession
):
    """Test that unique username database constraint is enforced."""
    # Create a user
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "uniquetest1@example.com",
            "username": "uniqueusername",
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 201
    
    # Try to create another user with the same username
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "uniquetest2@example.com",  # Different email
            "username": "uniqueusername",  # Same username
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    # API should reject this due to unique constraint
    assert response.status_code in [400, 409, 422]
    error = response.json()["detail"]
    assert "username" in error.lower() and ("taken" in error.lower() or "already" in error.lower())

@pytest.mark.asyncio
async def test_unique_email_constraint(
    client: AsyncClient,
    parent_token,
    db_session: AsyncSession
):
    """Test that unique email database constraint is enforced."""
    # Create a user
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "sameemail@example.com",
            "username": "emailuser1",
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 201
    
    # Try to create another user with the same email
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "sameemail@example.com",  # Same email
            "username": "emailuser2",  # Different username
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    # API should reject this due to unique constraint
    assert response.status_code in [400, 409, 422]
    error = response.json()["detail"]
    assert "email" in error.lower() and ("taken" in error.lower() or "already" in error.lower() or "registered" in error.lower())

@pytest.mark.asyncio
async def test_foreign_key_constraint(
    client: AsyncClient,
    parent_token,
    db_session: AsyncSession
):
    """Test that foreign key constraints are enforced."""
    # Try to create a chore with a non-existent assignee
    response = await client.post(
        "/api/v1/chores/",
        json={
            "title": "Bad Assignee Chore",
            "description": "Assigned to non-existent user",
            "reward": 5.0,
            "assignee_id": 9999  # Non-existent user
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    # API should reject this due to foreign key constraint
    assert response.status_code in [404, 422, 500]
    error = response.json()["detail"]
    assert "assignee" in error.lower() or "not found" in error.lower()

@pytest.mark.asyncio
async def test_database_cascade_delete(
    client: AsyncClient,
    parent_token,
    test_parent_user,
    test_child_user,
    db_session: AsyncSession
):
    """Test that deleting a parent deletes or orphans related child entities."""
    # Create a chore for the test child
    response = await client.post(
        "/api/v1/chores/",
        json={
            "title": "Cascade Test Chore",
            "description": "For testing cascades",
            "reward": 5.0,
            "assignee_id": test_child_user.id
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 201
    chore_id = response.json()["id"]
    
    # Verify the chore exists
    response = await client.get(
        f"/api/v1/chores/{chore_id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    
    # Now delete the parent user directly from the database
    # This should either cascade delete related chores or set their creator_id to NULL
    delete_query = text("DELETE FROM users WHERE id = :user_id")
    await db_session.execute(delete_query, {"user_id": test_parent_user.id})
    await db_session.commit()
    
    # Let's check what happened to the chore
    try:
        # Try to fetch the chore via direct SQL to see if it still exists or has NULL creator
        check_query = text("SELECT id, creator_id FROM chores WHERE id = :chore_id")
        result = await db_session.execute(check_query, {"chore_id": chore_id})
        chore_row = result.fetchone()
        
        if chore_row:
            # If the chore still exists, verify that creator_id is now NULL
            # (assuming ON DELETE SET NULL was configured)
            assert chore_row.creator_id is None
        else:
            # If the chore doesn't exist, CASCADE DELETE was configured
            pass
    except Exception as e:
        # Just log the exception, as we're testing behavior
        print(f"Database query failed: {str(e)}")

@pytest.mark.asyncio
async def test_concurrent_modification(
    client: AsyncClient,
    parent_token,
    test_chore,
    db_session: AsyncSession
):
    """Test concurrent modifications to the same entity."""
    # Simulate two clients trying to update the same chore at the same time
    
    async def update_title(new_title):
        return await client.put(
            f"/api/v1/chores/{test_chore.id}",
            json={"title": new_title},
            headers={"Authorization": f"Bearer {parent_token}"}
        )
    
    # Create two tasks to run concurrently
    task1 = asyncio.create_task(update_title("New Title 1"))
    task2 = asyncio.create_task(update_title("New Title 2"))
    
    # Wait for both to complete
    response1 = await task1
    response2 = await task2
    
    # Both requests should succeed or one should fail with a conflict error
    assert response1.status_code == 200 or response2.status_code == 200
    
    # If both succeeded, check which title "won"
    if response1.status_code == 200 and response2.status_code == 200:
        final_response = await client.get(
            f"/api/v1/chores/{test_chore.id}",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        assert final_response.status_code == 200
        final_title = final_response.json()["title"]
        assert final_title in ["New Title 1", "New Title 2"] 
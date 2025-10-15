import pytest
import pytest_asyncio
from httpx import AsyncClient
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.chore import Chore
from backend.app.models.user import User
from backend.app.core.config import settings

# Access the SECRET_KEY and ALGORITHM from settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

@pytest.mark.asyncio
async def test_expired_token(client: AsyncClient, test_parent_user):
    """Test behavior with an expired token."""
    # Create an expired token
    expire = datetime.utcnow() - timedelta(minutes=15)  # 15 minutes in the past
    payload = {"exp": expire, "sub": str(test_parent_user.id)}
    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Try to access an endpoint that requires authentication
    response = await client.get(
        "/api/v1/chores",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    error = response.json()["detail"]
    assert "expired" in error.lower() or "invalid" in error.lower()

@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    """Test behavior with an invalid token."""
    # Create an invalid token
    invalid_token = "invalid.token.string"
    
    # Try to access an endpoint that requires authentication
    response = await client.get(
        "/api/v1/chores",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    assert response.status_code == 401
    error = response.json()["detail"]
    assert "invalid" in error.lower() or "could not validate" in error.lower()

@pytest.mark.asyncio
async def test_missing_token(client: AsyncClient):
    """Test behavior with a missing token."""
    # Try to access an endpoint that requires authentication with no token
    response = await client.get("/api/v1/chores")
    assert response.status_code == 401
    error = response.json()["detail"]
    assert "not authenticated" in error.lower()

@pytest.mark.asyncio
async def test_non_existent_user_token(client: AsyncClient):
    """Test behavior with a token for a non-existent user."""
    # Create a token for a non-existent user
    expire = datetime.utcnow() + timedelta(minutes=30)
    payload = {"exp": expire, "sub": "999999"}  # Non-existent user ID
    nonexistent_user_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Try to access an endpoint that requires authentication
    response = await client.get(
        "/api/v1/chores",
        headers={"Authorization": f"Bearer {nonexistent_user_token}"}
    )
    assert response.status_code == 401
    error = response.json()["detail"]
    assert "user" in error.lower() and "not found" in error.lower()

@pytest.mark.asyncio
async def test_child_accessing_parent_only_endpoints(client: AsyncClient, child_token):
    """Test a child trying to access parent-only endpoints."""
    # Try to create a chore (parent-only operation) with multi-assignment mode
    response = await client.post(
        "/api/v1/chores",
        json={
            "title": "Test chore",
            "description": "Description",
            "reward": 5.0,
            "assignment_mode": "single",
            "assignee_ids": [2]  # Multi-assignment format
        },
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    error = response.json()["detail"]
    assert "only parents" in error.lower()

    # Try to access pending-approval endpoint (parent-only)
    response = await client.get(
        "/api/v1/chores/pending-approval",
        headers={"Authorization": f"Bearer {child_token}"}
    )
    assert response.status_code == 403
    error = response.json()["detail"]
    assert "only for parent" in error.lower()

@pytest.mark.asyncio
async def test_parent_accessing_child_only_endpoints(client: AsyncClient, parent_token):
    """Test a parent trying to access child-only endpoints."""
    # Try to access available chores endpoint (child-only)
    response = await client.get(
        "/api/v1/chores/available",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 403
    error = response.json()["detail"]
    assert "only for children" in error.lower()

@pytest.mark.asyncio
async def test_cross_account_access(
    client: AsyncClient, 
    parent_token, 
    test_parent_user,
    db_session: AsyncSession
):
    """Test attempt to access data from another account."""
    # Create a second parent user and child
    second_parent = User(
        email="second_parent@example.com",
        username="second_parent",
        hashed_password="$2b$12$wBgFaxkRQHECnV9g6ZwK5OezOXbIUJjnHbGudS6xHN49YAPG7Fkhy",  # "password123"
        is_active=True,
        is_parent=True
    )
    db_session.add(second_parent)
    await db_session.commit()
    await db_session.refresh(second_parent)
    
    second_child = User(
        email="second_child@example.com",
        username="second_child",
        hashed_password="$2b$12$wBgFaxkRQHECnV9g6ZwK5OezOXbIUJjnHbGudS6xHN49YAPG7Fkhy",  # "password123"
        is_active=True,
        is_parent=False,
        parent_id=second_parent.id
    )
    db_session.add(second_child)
    await db_session.commit()
    await db_session.refresh(second_child)
    
    # Create a chore for the second parent's child with multi-assignment
    from backend.app.models.chore_assignment import ChoreAssignment

    second_chore = Chore(
        title="Second parent's chore",
        description="Created by second parent",
        reward=5.00,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_disabled=False,
        assignment_mode="single",
        creator_id=second_parent.id
    )
    db_session.add(second_chore)
    await db_session.flush()  # Get chore ID

    # Create assignment
    assignment = ChoreAssignment(
        chore_id=second_chore.id,
        assignee_id=second_child.id,
        is_completed=False,
        is_approved=False
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(second_chore)
    
    # First parent tries to access the second parent's child's chores
    response = await client.get(
        f"/api/v1/chores/child/{second_child.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 404
    error = response.json()["detail"]
    assert "not found" in error.lower() or "not your child" in error.lower()
    
    # First parent tries to access the second parent's chore
    response = await client.get(
        f"/api/v1/chores/{second_chore.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    # Either it returns 404 "not found" or 403 "not authorized"
    assert response.status_code in [403, 404]
    
    # First parent tries to update the second parent's chore
    response = await client.put(
        f"/api/v1/chores/{second_chore.id}",
        json={"title": "Hacked chore"},
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code in [403, 404] 
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_user_registration_success(client: AsyncClient, parent_token):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert data["is_parent"] == False

@pytest.mark.asyncio
async def test_user_registration_invalid_email(client: AsyncClient, parent_token):
    """Test user registration with invalid email format."""
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "invalidemail",  # Invalid format
            "username": "invaliduser",
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Check that the error relates to email validation
    assert any("email" in error["loc"] for error in data["detail"])

@pytest.mark.asyncio
async def test_user_registration_missing_fields(client: AsyncClient, parent_token):
    """Test user registration with missing required fields."""
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "missingfields"
            # Missing email, password, etc.
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Check which fields are reported as missing
    missing_fields = [error["loc"][1] for error in data["detail"]]
    assert "email" in missing_fields
    assert "password" in missing_fields

@pytest.mark.asyncio
async def test_user_registration_duplicate_email(client: AsyncClient, parent_token, test_parent_user):
    """Test user registration with an email that already exists."""
    # First request should succeed
    response1 = await client.post(
        "/api/v1/users/",
        json={
            "email": "unique@example.com",
            "username": "uniqueuser",
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response1.status_code == 201
    
    # Second request with same email should fail
    response2 = await client.post(
        "/api/v1/users/",
        json={
            "email": "unique@example.com",  # Same as above
            "username": "anotheruser",
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response2.status_code in [400, 409]

@pytest.mark.asyncio
async def test_user_registration_duplicate_username(client: AsyncClient, parent_token):
    """Test user registration with a username that already exists."""
    # First request should succeed
    response1 = await client.post(
        "/api/v1/users/",
        json={
            "email": "user1@example.com",
            "username": "sameusername",
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response1.status_code == 201
    
    # Second request with same username should fail
    response2 = await client.post(
        "/api/v1/users/",
        json={
            "email": "user2@example.com",
            "username": "sameusername",  # Same as above
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response2.status_code in [400, 409]

@pytest.mark.asyncio
async def test_user_registration_invalid_parent_id(client: AsyncClient, parent_token):
    """Test user registration with an invalid parent_id."""
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "childuser@example.com",
            "username": "childuser",
            "password": "password123",
            "is_parent": False,
            "parent_id": 9999  # Non-existent parent ID
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 404  # Not found
    assert "Parent user not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_user_registration_password_too_short(client: AsyncClient, parent_token):
    """Test user registration with a password that's too short."""
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "shortpw@example.com",
            "username": "shortpw",
            "password": "short",  # Too short
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 422
    assert "Password must be at least 8 characters long" in response.json()["detail"]

@pytest.mark.asyncio
async def test_user_registration_child_creates_user(client: AsyncClient, child_token):
    """Test that a child user cannot create another user."""
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "unauthorized@example.com",
            "username": "unauthorized",
            "password": "password123",
            "is_parent": False,
            "parent_id": 1
        },
        headers={"Authorization": f"Bearer {child_token}"}
    )
    # This should be forbidden (403) if your API checks for parent status
    assert response.status_code == 403
    assert "Only parents can create new users" in response.json()["detail"] 
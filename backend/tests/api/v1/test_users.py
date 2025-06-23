import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    # Test valid registration
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "is_parent": "true"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert data["is_parent"] == True
    assert "id" in data

    # Test duplicate email
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "newuser@example.com",
            "username": "differentuser",
            "password": "password123",
            "is_parent": "true"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

    # Test duplicate username
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "different@example.com",
            "username": "newuser",
            "password": "password123",
            "is_parent": "true"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, test_parent_user):
    """Test user login."""
    # Test valid login
    response = await client.post(
        "/api/v1/users/login",
        data={
            "username": "parent_user",
            "password": "password123"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test invalid password
    response = await client.post(
        "/api/v1/users/login",
        data={
            "username": "parent_user",
            "password": "wrongpassword"
        },
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

    # Test non-existent user
    response = await client.post(
        "/api/v1/users/login",
        data={
            "username": "nonexistent",
            "password": "password123"
        },
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_read_users(client: AsyncClient, parent_token, test_parent_user, test_child_user):
    """Test getting all users."""
    response = await client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Our two test users
    user_emails = [user["email"] for user in data]
    assert "parent@example.com" in user_emails
    assert "child@example.com" in user_emails


@pytest.mark.asyncio
async def test_read_children(client: AsyncClient, parent_token, test_parent_user, test_child_user):
    """Test getting all children for a parent."""
    response = await client.get(
        f"/api/v1/users/children/{test_parent_user.id}",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # Our one test child
    assert data[0]["email"] == "child@example.com"
    assert data[0]["username"] == "child_user"
    assert data[0]["is_parent"] == False 
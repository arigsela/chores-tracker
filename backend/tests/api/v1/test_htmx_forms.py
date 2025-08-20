import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_register_form_submission_success(client: AsyncClient):
    """Test the successful submission of the registration form."""
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
    print(f"\nRegister form error: {response.status_code}")
    print(f"Response detail: {response.text}")
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert data["is_parent"] == True

@pytest.mark.asyncio
async def test_register_form_submission_invalid_email(client: AsyncClient):
    """Test form validation for invalid email format."""
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "invalid-email",  # Invalid format
            "username": "invaliduser",
            "password": "password123",
            "is_parent": "true"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()
    assert "Invalid email format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_register_form_submission_missing_fields(client: AsyncClient):
    """Test form validation for missing required fields."""
    response = await client.post(
        "/api/v1/users/register",
        data={
            "username": "missingfields"
            # Missing email, password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_add_child_form_submission_success(client: AsyncClient, parent_token):
    """Test the successful submission of the add child form."""
    # First get current user ID to use as parent_id
    user_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    parent_id = user_response.json()["id"]
    
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "newchild@example.com",
            "username": "newchild",
            "password": "password123",
            "is_parent": "false",
            "parent_id": str(parent_id)
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {parent_token}"
        }
    )
    print(f"\nAdd child form error: {response.status_code}")
    print(f"Response detail: {response.text}")
    assert response.status_code == 201
    # Now expecting JSON response since we converted to REST API
    data = response.json()
    assert data["username"] == "newchild"
    assert data["is_parent"] == False
    assert data["parent_id"] == parent_id

@pytest.mark.asyncio
async def test_add_child_form_submission_missing_parent_id(client: AsyncClient, parent_token):
    """Test that child form without parent_id works when authorized."""
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "childnoparent@example.com",
            "username": "childnoparent",
            "password": "password123",
            "is_parent": "false"
            # Missing parent_id, but providing token
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {parent_token}"
        }
    )
    # The endpoint should automatically use the parent_id from the token
    assert response.status_code == 201
    # Now expecting JSON response since we converted to REST API
    data = response.json()
    assert data["username"] == "childnoparent"
    assert data["is_parent"] == False
    assert data["parent_id"] is not None  # Should be set from token

@pytest.mark.asyncio
async def test_login_form_submission_success(client: AsyncClient, test_parent_user):
    """Test the successful submission of the login form."""
    response = await client.post(
        "/api/v1/users/login",
        data={
            "username": test_parent_user.username,
            "password": "password123"  # This is the password from the fixture
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_form_submission_invalid_credentials(client: AsyncClient):
    """Test login form with invalid credentials."""
    response = await client.post(
        "/api/v1/users/login",
        data={
            "username": "nonexistent",
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data 
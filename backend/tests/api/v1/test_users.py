import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_with_codes(client: AsyncClient):
    """Test user registration with registration codes (BETA feature)."""
    # Test parent registration without code (should fail)
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "nocode@example.com",
            "username": "nocode",
            "password": "password123",
            "is_parent": "true"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 422
    assert "Registration code is required during beta period" in response.json()["detail"]

    # Test parent registration with invalid code (should fail)
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "badcode@example.com",
            "username": "badcode",
            "password": "password123",
            "is_parent": "true",
            "registration_code": "INVALID_CODE"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 422
    assert "Invalid registration code" in response.json()["detail"]

    # Test valid parent registration with code
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "is_parent": "true",
            "registration_code": "BETA2024"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert data["is_parent"] == True
    assert "id" in data

    # Test duplicate email (with valid code)
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "newuser@example.com",
            "username": "differentuser",
            "password": "password123",
            "is_parent": "true",
            "registration_code": "BETA2024"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

    # Test duplicate username (with valid code)
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "different@example.com",
            "username": "newuser",
            "password": "password123",
            "is_parent": "true",
            "registration_code": "BETA2024"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]

    # Test case-insensitive codes
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "lowercase@example.com",
            "username": "lowercase",
            "password": "password123",
            "is_parent": "true",
            "registration_code": "beta2024"  # lowercase
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "lowercase"


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration (legacy test name for backward compatibility)."""
    # This test now includes registration code for parent accounts
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "legacy@example.com",
            "username": "legacy",
            "password": "password123",
            "is_parent": "true",
            "registration_code": "BETA2024"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "legacy@example.com"
    assert data["username"] == "legacy"
    assert data["is_parent"] == True
    assert "id" in data


@pytest.mark.asyncio 
async def test_child_registration_no_code_needed(client: AsyncClient, parent_token, test_parent_user):
    """Test that child registration still works without registration codes."""
    # Child registration via form should work without code
    response = await client.post(
        "/api/v1/users/register",
        data={
            "username": "testchild",
            "password": "childpass",
            "is_parent": "false"
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {parent_token}"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testchild"
    assert data["is_parent"] == False
    assert data["parent_id"] == test_parent_user.id

    # Child registration via JSON API should also work without code
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "jsonchild",
            "password": "childpass",
            "is_parent": False
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "jsonchild"
    assert data["is_parent"] == False
    assert data["parent_id"] == test_parent_user.id


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


@pytest.mark.asyncio
async def test_read_my_children(client: AsyncClient, parent_token, test_parent_user, test_child_user):
    """Test getting children for current parent via convenience endpoint."""
    response = await client.get(
        "/api/v1/users/my-children",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(u["id"] == test_child_user.id for u in data)


@pytest.mark.asyncio
async def test_allowance_summary(client: AsyncClient, parent_token, test_parent_user, test_child_user):
    """Test allowance summary for current parent returns expected shape."""
    response = await client.get(
        "/api/v1/users/allowance-summary",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        # Minimal shape checks
        assert {"id", "username", "completed_chores", "total_earned", "total_adjustments", "paid_out", "balance_due"}.issubset(item.keys())


@pytest.mark.asyncio
async def test_admin_registration_status(client: AsyncClient, parent_token):
    """Test the admin registration status endpoint."""
    response = await client.get(
        "/api/v1/users/admin/registration-status",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check expected fields
    expected_fields = {"registration_restricted", "valid_codes_count", "valid_codes", "message"}
    assert expected_fields.issubset(data.keys())
    
    # Check data types and values
    assert isinstance(data["registration_restricted"], bool)
    assert isinstance(data["valid_codes_count"], int)
    assert isinstance(data["valid_codes"], list)
    assert isinstance(data["message"], str)
    
    # Should be restricted during tests (default codes are configured)
    assert data["registration_restricted"] == True
    assert data["valid_codes_count"] == 3
    assert "BETA2024" in data["valid_codes"]
    assert "FAMILY_TRIAL" in data["valid_codes"]
    assert "CHORES_BETA" in data["valid_codes"]
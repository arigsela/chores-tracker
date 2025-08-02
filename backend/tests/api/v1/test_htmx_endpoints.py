import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint renders correctly."""
    response = await client.get("/")
    assert response.status_code == 200
    assert b"Chores Tracker" in response.content  # Check that the page contains the expected title

@pytest.mark.asyncio
async def test_dashboard_endpoint_unauthorized(client: AsyncClient):
    """Test the dashboard endpoint always returns 200 even when unauthorized."""
    response = await client.get("/dashboard")
    assert response.status_code == 200
    # Dashboard page now handles authentication via JavaScript, so it always returns 200

@pytest.mark.asyncio
async def test_dashboard_endpoint_authorized(client: AsyncClient, parent_token):
    """Test the dashboard endpoint returns 200 when authorized."""
    response = await client.get(
        "/dashboard", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    assert b"Dashboard" in response.content

@pytest.mark.asyncio
async def test_pages_endpoint(client: AsyncClient):
    """Test the pages endpoint renders correctly."""
    response = await client.get("/pages/login")
    assert response.status_code == 200
    assert b"Login" in response.content

@pytest.mark.asyncio
async def test_components_endpoint(client: AsyncClient):
    """Test the components endpoint renders correctly."""
    # This may require creating a test component first
    response = await client.get("/components/chore_list")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_users_me_endpoint(client: AsyncClient, parent_token):
    """Test the users/me endpoint returns the current user."""
    response = await client.get(
        "/api/v1/users/me", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert data["is_parent"] == True

@pytest.mark.asyncio
async def test_children_options_endpoint(client: AsyncClient, parent_token, test_child_user):
    """Test the children dropdown options endpoint."""
    response = await client.get(
        "/api/v1/users/children", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    # Updated test to match new clickable card format
    assert b"Click to view chores" in response.content
    assert str(test_child_user.id).encode() in response.content
    assert test_child_user.username.encode() in response.content
    assert b"viewChildChores" in response.content

@pytest.mark.asyncio
async def test_allowance_summary_endpoint(client: AsyncClient, parent_token, test_child_user):
    """Test the allowance summary endpoint."""
    response = await client.get(
        "/api/v1/users/summary", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    assert test_child_user.username.encode() in response.content

@pytest.mark.asyncio
async def test_chores_html_endpoint(client: AsyncClient, parent_token, test_chore):
    """Test the chores HTML endpoint with various filters."""
    # Test active chores
    response = await client.get(
        "/api/v1/chores?status=active", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    
    # Test pending chores
    response = await client.get(
        "/api/v1/chores?status=pending", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    
    # Test completed chores
    response = await client.get(
        "/api/v1/chores?status=completed", 
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_user_creation_form_submission(client: AsyncClient, parent_token, db_session: AsyncSession):
    """Test the user creation form submission."""
    # Get the user form first
    response = await client.get(
        "/pages/user-form",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    
    # Now submit the form to create a new child user
    response = await client.post(
        "/api/v1/users/register",
        data={
            "email": "newchild@example.com",
            "username": "newchild",
            "password": "password123",
            "is_parent": "false",
            "parent_id": "1"  # Assuming parent id is 1
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {parent_token}"
        }
    )
    assert response.status_code == 201
    # Expecting HTML response, not JSON
    assert "Success" in response.text
    assert "newchild" in response.text
    
    # Test with invalid data to check 422 error
    response = await client.post(
        "/api/v1/users/register",
        json={
            "email": "invalid-email",  # Invalid email format
            "username": "another-child",
            "password": "password123",
            "is_parent": False
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 422  # Validation error
    
    # Test with missing required fields
    response = await client.post(
        "/api/v1/users/register",
        json={
            "username": "missing-fields",
            "is_parent": False
        },
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 422  # Validation error 
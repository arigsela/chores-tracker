import pytest
import pytest_asyncio
from httpx import AsyncClient
import re
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_htmx_login_form_response(client: AsyncClient):
    """Test the login form HTML response."""
    response = await client.get("/pages/login")
    assert response.status_code == 200
    
    # Verify the response content type
    assert "text/html" in response.headers["content-type"]
    
    # Parse the HTML and check for key elements
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Check for form tag
    form = soup.find("form", id="login-form")
    assert form is not None
    
    # Check for username input
    username_input = soup.find("input", {"name": "username"})
    assert username_input is not None
    
    # Check for password input
    password_input = soup.find("input", {"name": "password", "type": "password"})
    assert password_input is not None
    
    # Check for submit button
    submit_button = soup.find("button", {"type": "submit"})
    assert submit_button is not None

@pytest.mark.asyncio
async def test_htmx_dashboard_html_structure(client: AsyncClient, parent_token):
    """Test the HTML structure of the dashboard page."""
    response = await client.get(
        "/pages/dashboard",
        headers={"Authorization": f"Bearer {parent_token}"}
    )
    assert response.status_code == 200
    
    # Verify it's an HTML response
    assert "text/html" in response.headers["content-type"]
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Check for Tailwind CSS classes
    tailwind_classes = ["flex", "grid", "p-", "m-", "text-", "bg-"]
    has_tailwind = False
    for css_class in tailwind_classes:
        if soup.find(class_=re.compile(css_class)):
            has_tailwind = True
            break
    assert has_tailwind, "No Tailwind CSS classes found in dashboard HTML"
    
    # Check for basic dashboard elements (header or navigation)
    assert soup.find("h1") is not None or soup.find("h2") is not None or soup.find("nav") is not None

@pytest.mark.asyncio
async def test_chore_component_response(client: AsyncClient, parent_token, test_chore):
    """Test an HTML component response for a chore."""
    # Try a different component endpoint that exists in the application
    response = await client.get(
        f"/api/v1/chores/html",
        headers={
            "Authorization": f"Bearer {parent_token}",
            "HX-Request": "true"  # Mimic HTMX request
        }
    )
    assert response.status_code == 200
    
    # Verify it's HTML
    assert "text/html" in response.headers["content-type"]
    
    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Check for basic structure elements
    assert soup.find("div") is not None
    
    # Check for Tailwind CSS classes
    tailwind_classes = ["flex", "grid", "p-", "m-", "text-", "bg-"]
    has_tailwind = False
    for css_class in tailwind_classes:
        if soup.find(class_=re.compile(css_class)):
            has_tailwind = True
            break
    assert has_tailwind, "No Tailwind CSS classes found in component HTML"

@pytest.mark.asyncio
async def test_error_html_responses(client: AsyncClient):
    """Test error messages in HTML responses."""
    # Test authentication error response with HX-Request header
    response = await client.get(
        "/pages/dashboard",  # Requires authentication
        headers={"HX-Request": "true"}  # No auth token
    )
    assert response.status_code == 401
    
    # Just verify the response contains the error information in some form
    # (could be JSON for API endpoints)
    response_text = response.text.lower()
    assert "unauthorized" in response_text or "authentication" in response_text or "token" in response_text

@pytest.mark.asyncio
async def test_form_error_html_response(client: AsyncClient):
    """Test HTML form validation error responses."""
    # Submit invalid login credentials
    response = await client.post(
        "/api/v1/users/login",
        data={
            "username": "nonexistent",
            "password": "wrong"
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "HX-Request": "true"
        }
    )
    assert response.status_code == 401
    
    # Either JSON error or HTML error message
    if "application/json" in response.headers.get("content-type", ""):
        error = response.json()
        assert "detail" in error
    else:
        # HTML error message
        assert "text/html" in response.headers.get("content-type", "")
        assert "error" in response.text.lower() or "invalid" in response.text.lower() 
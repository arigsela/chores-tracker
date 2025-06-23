"""
Tests for main.py endpoints.
"""
import pytest


class TestMainEndpoints:
    """Test main.py endpoints."""
    
    @pytest.mark.asyncio
    async def test_healthcheck(self, client):
        """Test healthcheck endpoint."""
        response = await client.get("/api/v1/healthcheck")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    @pytest.mark.asyncio
    async def test_index_page(self, client):
        """Test index page."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_dashboard_page(self, client):
        """Test dashboard page."""
        response = await client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_chores_page(self, client):
        """Test chores page."""
        response = await client.get("/chores")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_users_page(self, client):
        """Test users page."""
        response = await client.get("/users")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_reports_page(self, client):
        """Test reports page."""
        response = await client.get("/reports")
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("text/html")
    
    @pytest.mark.asyncio
    async def test_specific_page_login(self, client):
        """Test specific page route with login page."""
        response = await client.get("/pages/login")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_nonexistent_page(self, client):
        """Test non-existent page returns 404."""
        response = await client.get("/pages/nonexistent")
        assert response.status_code == 404
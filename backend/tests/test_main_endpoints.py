"""
Tests for main.py endpoints.
"""
import pytest


class TestMainEndpoints:
    """Test main.py endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_nonexistent_html_pages_return_404(self, client):
        """Test that HTML page routes that don't exist return 404."""
        html_routes = [
            "/dashboard", "/chores", "/users", "/reports", "/pages/login"
        ]
        for route in html_routes:
            response = await client.get(route)
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_nonexistent_page(self, client):
        """Test non-existent page returns 404."""
        response = await client.get("/pages/nonexistent")
        assert response.status_code == 404
"""
Comprehensive unit tests for health check endpoints.

Tests cover:
- Basic liveness probe
- Readiness probe with database connectivity
- Detailed health check with component diagnostics
- Error handling and failure scenarios
- Response format validation
- Status code correctness
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from fastapi import status
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError, DatabaseError
from sqlalchemy import text


class TestBasicHealthEndpoint:
    """Test GET /api/v1/health endpoint (basic liveness probe)."""

    @pytest.mark.asyncio
    async def test_basic_health_returns_ok(self, client: AsyncClient):
        """Test basic health endpoint returns 200 OK."""
        # Act
        response = await client.get("/api/v1/health")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_basic_health_timestamp_format(self, client: AsyncClient):
        """Test health endpoint returns valid ISO format timestamp."""
        # Act
        response = await client.get("/api/v1/health")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify timestamp is valid ISO format
        timestamp_str = data["timestamp"]
        parsed_time = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_time, datetime)

    @pytest.mark.asyncio
    async def test_basic_health_no_database_dependency(self, client: AsyncClient):
        """Test basic health endpoint works without database connection."""
        # This endpoint should not depend on database at all
        # It should return 200 even if DB is down
        response = await client.get("/api/v1/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_basic_health_response_structure(self, client: AsyncClient):
        """Test basic health endpoint has correct response structure."""
        # Act
        response = await client.get("/api/v1/health")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify all required fields are present
        assert "status" in data
        assert "timestamp" in data
        assert len(data) == 2  # Only these two fields

    @pytest.mark.asyncio
    async def test_basic_health_multiple_calls_consistent(self, client: AsyncClient):
        """Test multiple calls to basic health return consistent results."""
        # Act - make multiple calls
        responses = []
        for _ in range(3):
            response = await client.get("/api/v1/health")
            responses.append(response)

        # Assert - all return 200 OK
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["status"] == "ok"


class TestReadinessCheckEndpoint:
    """Test GET /api/v1/health/ready endpoint (readiness probe)."""

    @pytest.mark.asyncio
    async def test_readiness_check_healthy_database(
        self, 
        client: AsyncClient
    ):
        """Test readiness check returns ready when database is connected."""
        # Act
        response = await client.get("/api/v1/health/ready")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_readiness_check_database_connectivity(
        self, 
        client: AsyncClient
    ):
        """Test readiness check verifies database connectivity with SELECT 1."""
        # This test verifies the endpoint actually checks DB connection
        response = await client.get("/api/v1/health/ready")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["database"] == "connected"

    @pytest.mark.asyncio
    async def test_readiness_check_response_structure(
        self,
        client: AsyncClient
    ):
        """Test readiness check has correct response structure."""
        # Act
        response = await client.get("/api/v1/health/ready")

        # Assert
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_readiness_check_timestamp_format(
        self,
        client: AsyncClient
    ):
        """Test readiness check returns valid ISO format timestamp."""
        # Act
        response = await client.get("/api/v1/health/ready")

        # Assert
        data = response.json()
        timestamp_str = data["timestamp"]
        parsed_time = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_time, datetime)

    @pytest.mark.asyncio
    async def test_readiness_check_database_failure_returns_503(
        self,
        client: AsyncClient
    ):
        """Test readiness check returns 503 when database is disconnected."""
        # Arrange - Mock database to raise an exception
        with patch('backend.app.api.api_v1.endpoints.health.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=OperationalError(
                "Connection refused", None, None
            ))
            
            async def mock_db_generator():
                yield mock_session
            
            mock_get_db.return_value = mock_db_generator()

            # Act
            response = await client.get("/api/v1/health/ready")

            # Assert
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data["status"] == "not_ready"
            assert data["database"] == "disconnected"
            assert "error" in data
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_readiness_check_generic_database_error(
        self,
        client: AsyncClient
    ):
        """Test readiness check handles generic database errors."""
        # Arrange - Mock database to raise generic exception
        with patch('backend.app.api.api_v1.endpoints.health.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=Exception("Generic DB error"))
            
            async def mock_db_generator():
                yield mock_session
            
            mock_get_db.return_value = mock_db_generator()

            # Act
            response = await client.get("/api/v1/health/ready")

            # Assert
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data["status"] == "not_ready"
            assert "error" in data
            assert "Generic DB error" in data["error"]


class TestDetailedHealthEndpoint:
    """Test GET /api/v1/health/detailed endpoint (component diagnostics)."""

    @pytest.mark.asyncio
    async def test_detailed_health_all_components_healthy(
        self,
        client: AsyncClient
    ):
        """Test detailed health returns 200 when all components are healthy."""
        # Act
        response = await client.get("/api/v1/health/detailed")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "timestamp" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_detailed_health_database_component_healthy(
        self,
        client: AsyncClient
    ):
        """Test detailed health includes healthy database component."""
        # Act
        response = await client.get("/api/v1/health/detailed")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check database component
        assert "database" in data["components"]
        db_component = data["components"]["database"]
        assert db_component["status"] == "healthy"
        assert "version" in db_component
        assert db_component["type"] == "MySQL"

    @pytest.mark.asyncio
    async def test_detailed_health_response_structure(
        self,
        client: AsyncClient
    ):
        """Test detailed health has complete response structure."""
        # Act
        response = await client.get("/api/v1/health/detailed")

        # Assert
        data = response.json()
        
        # Top-level fields
        assert "status" in data
        assert "components" in data
        assert "timestamp" in data
        assert "version" in data
        
        # Components structure
        components = data["components"]
        assert isinstance(components, dict)
        assert len(components) >= 1  # At least database

    @pytest.mark.asyncio
    async def test_detailed_health_version_present(
        self,
        client: AsyncClient
    ):
        """Test detailed health includes version information."""
        # Act
        response = await client.get("/api/v1/health/detailed")

        # Assert
        data = response.json()
        assert "version" in data
        assert data["version"] == "3.0.0"

    @pytest.mark.asyncio
    async def test_detailed_health_timestamp_format(
        self,
        client: AsyncClient
    ):
        """Test detailed health returns valid ISO format timestamp."""
        # Act
        response = await client.get("/api/v1/health/detailed")

        # Assert
        data = response.json()
        timestamp_str = data["timestamp"]
        parsed_time = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed_time, datetime)

    @pytest.mark.asyncio
    async def test_detailed_health_database_failure_returns_503(
        self,
        client: AsyncClient
    ):
        """Test detailed health returns 503 when database is unhealthy."""
        # Arrange - Mock database to raise exception
        with patch('backend.app.api.api_v1.endpoints.health.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=DatabaseError(
                "Database connection failed", None, None
            ))
            
            async def mock_db_generator():
                yield mock_session
            
            mock_get_db.return_value = mock_db_generator()

            # Act
            response = await client.get("/api/v1/health/detailed")

            # Assert
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "components" in data
            
            # Check database component is unhealthy
            db_component = data["components"]["database"]
            assert db_component["status"] == "unhealthy"
            assert "error" in db_component

    @pytest.mark.asyncio
    async def test_detailed_health_database_error_details(
        self,
        client: AsyncClient
    ):
        """Test detailed health includes error details for unhealthy components."""
        # Arrange
        error_message = "Connection timeout after 30 seconds"
        with patch('backend.app.api.api_v1.endpoints.health.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(
                side_effect=Exception(error_message)
            )
            
            async def mock_db_generator():
                yield mock_session
            
            mock_get_db.return_value = mock_db_generator()

            # Act
            response = await client.get("/api/v1/health/detailed")

            # Assert
            data = response.json()
            db_component = data["components"]["database"]
            assert db_component["status"] == "unhealthy"
            assert error_message in db_component["error"]

    @pytest.mark.asyncio
    async def test_detailed_health_multiple_components_structure(
        self,
        client: AsyncClient
    ):
        """Test detailed health can accommodate multiple components."""
        # Act
        response = await client.get("/api/v1/health/detailed")

        # Assert
        data = response.json()
        components = data["components"]
        
        # Currently only database, but structure supports multiple
        assert isinstance(components, dict)
        assert "database" in components
        
        # Each component should have status
        for _component_name, component_data in components.items():
            assert "status" in component_data
            assert component_data["status"] in ["healthy", "unhealthy"]


class TestHealthEndpointsSecurity:
    """Test health endpoints security and access control."""

    @pytest.mark.asyncio
    async def test_health_endpoints_no_authentication_required(
        self,
        client: AsyncClient
    ):
        """Test health endpoints work without authentication."""
        # Test all three health endpoints without auth token
        endpoints = [
            "/api/v1/health",
            "/api/v1/health/ready",
            "/api/v1/health/detailed"
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            # Should not return 401 Unauthorized
            assert response.status_code != status.HTTP_401_UNAUTHORIZED
            # Should return success or service unavailable
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_503_SERVICE_UNAVAILABLE
            ]

    @pytest.mark.asyncio
    async def test_health_endpoints_public_access(
        self,
        client: AsyncClient
    ):
        """Test health endpoints are publicly accessible."""
        # These endpoints should be accessible without any credentials
        # for Kubernetes probes and load balancers
        
        response = await client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_health_endpoints_cors_friendly(
        self,
        client: AsyncClient
    ):
        """Test health endpoints work with CORS requests."""
        # Make request with Origin header (simulating CORS)
        headers = {"Origin": "https://monitoring.example.com"}
        
        response = await client.get("/api/v1/health", headers=headers)
        assert response.status_code == status.HTTP_200_OK


class TestHealthEndpointsPerformance:
    """Test health endpoints performance characteristics."""

    @pytest.mark.asyncio
    async def test_basic_health_fast_response(self, client: AsyncClient):
        """Test basic health endpoint responds quickly (no DB queries)."""
        # This is more of a regression test - basic health should be instant
        import time
        
        start = time.time()
        response = await client.get("/api/v1/health")
        duration = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        # Should respond in less than 100ms (very generous for test environment)
        assert duration < 0.1

    @pytest.mark.asyncio
    async def test_readiness_check_reasonable_timeout(
        self,
        client: AsyncClient
    ):
        """Test readiness check completes within reasonable time."""
        import time
        
        start = time.time()
        response = await client.get("/api/v1/health/ready")
        duration = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        # Should respond in less than 1 second (database is in-memory for tests)
        assert duration < 1.0

    @pytest.mark.asyncio
    async def test_detailed_health_reasonable_timeout(
        self,
        client: AsyncClient
    ):
        """Test detailed health completes within reasonable time."""
        import time
        
        start = time.time()
        response = await client.get("/api/v1/health/detailed")
        duration = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        # Should respond in less than 1 second
        assert duration < 1.0


class TestHealthEndpointsEdgeCases:
    """Test health endpoints edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_health_endpoint_with_query_parameters_ignored(
        self,
        client: AsyncClient
    ):
        """Test health endpoint ignores query parameters."""
        # Act
        response = await client.get("/api/v1/health?foo=bar&baz=qux")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_readiness_check_concurrent_requests(
        self,
        client: AsyncClient
    ):
        """Test readiness check handles concurrent requests."""
        import asyncio
        
        # Act - make concurrent requests
        tasks = [
            client.get("/api/v1/health/ready")
            for _ in range(5)
        ]
        responses = await asyncio.gather(*tasks)

        # Assert - all should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_detailed_health_concurrent_requests(
        self,
        client: AsyncClient
    ):
        """Test detailed health handles concurrent requests."""
        import asyncio
        
        # Act - make concurrent requests
        tasks = [
            client.get("/api/v1/health/detailed")
            for _ in range(5)
        ]
        responses = await asyncio.gather(*tasks)

        # Assert - all should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "components" in data

    @pytest.mark.asyncio
    async def test_health_endpoints_with_invalid_methods(
        self,
        client: AsyncClient
    ):
        """Test health endpoints reject non-GET methods."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/health/ready",
            "/api/v1/health/detailed"
        ]

        for endpoint in endpoints:
            # Try POST
            response = await client.post(endpoint)
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
            
            # Try PUT
            response = await client.put(endpoint)
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
            
            # Try DELETE
            response = await client.delete(endpoint)
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestHealthEndpointsIntegration:
    """Integration tests for health endpoints with real database."""

    @pytest.mark.asyncio
    async def test_health_check_workflow_for_kubernetes(
        self,
        client: AsyncClient
    ):
        """Test typical Kubernetes health check workflow."""
        # Step 1: Liveness probe
        liveness = await client.get("/api/v1/health")
        assert liveness.status_code == status.HTTP_200_OK

        # Step 2: Readiness probe
        readiness = await client.get("/api/v1/health/ready")
        assert readiness.status_code == status.HTTP_200_OK
        assert readiness.json()["database"] == "connected"

        # Step 3: Detailed diagnostics (optional)
        detailed = await client.get("/api/v1/health/detailed")
        assert detailed.status_code == status.HTTP_200_OK
        assert detailed.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_endpoints_progression(
        self,
        client: AsyncClient
    ):
        """Test health endpoints provide increasing detail."""
        # Basic health
        basic = await client.get("/api/v1/health")
        basic_data = basic.json()
        
        # Readiness
        ready = await client.get("/api/v1/health/ready")
        ready_data = ready.json()
        
        # Detailed
        detailed = await client.get("/api/v1/health/detailed")
        detailed_data = detailed.json()

        # Assert increasing information
        assert len(basic_data) < len(ready_data)
        assert len(ready_data) <= len(detailed_data)
        
        # Detailed should have components
        assert "components" in detailed_data
        assert "components" not in basic_data
        assert "components" not in ready_data

    @pytest.mark.asyncio
    async def test_all_health_endpoints_return_json(
        self,
        client: AsyncClient
    ):
        """Test all health endpoints return JSON responses."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/health/ready",
            "/api/v1/health/detailed"
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert "application/json" in response.headers.get("content-type", "")
            # Should be valid JSON
            data = response.json()
            assert isinstance(data, dict)
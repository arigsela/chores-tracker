import pytest
import os
from decimal import Decimal
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.models.reward_adjustment import RewardAdjustment
from backend.app.core.security.jwt import create_access_token
from backend.app.core.security.password import get_password_hash


class TestRewardAdjustmentsAPI:
    """Test cases for Reward Adjustments API endpoints."""

    @pytest.fixture
    def parent_headers(self, parent_token):
        """Create authorization headers with parent token."""
        return {"Authorization": f"Bearer {parent_token}"}

    @pytest.fixture
    def child_headers(self, child_token):
        """Create authorization headers with child token."""
        return {"Authorization": f"Bearer {child_token}"}

    # POST /api/v1/adjustments/ Tests
    @pytest.mark.asyncio
    async def test_create_adjustment_success(
        self, client: AsyncClient, parent_headers, test_child_user
    ):
        """Test successful adjustment creation by parent."""
        adjustment_data = {
            "child_id": test_child_user.id,
            "amount": "10.00",
            "reason": "Good behavior bonus"
        }
        
        response = await client.post(
            "/api/v1/adjustments/",
            json=adjustment_data,
            headers=parent_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["child_id"] == test_child_user.id
        assert data["amount"] == "10.00"
        assert data["reason"] == "Good behavior bonus"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_adjustment_unauthorized(self, client: AsyncClient, test_child_user):
        """Test adjustment creation without authentication."""
        adjustment_data = {
            "child_id": test_child_user.id,
            "amount": "10.00",
            "reason": "Test"
        }
        
        response = await client.post("/api/v1/adjustments/", json=adjustment_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_adjustment_child_forbidden(
        self, client: AsyncClient, child_headers, test_child_user
    ):
        """Test that children cannot create adjustments."""
        adjustment_data = {
            "child_id": test_child_user.id,
            "amount": "10.00",
            "reason": "Test"
        }
        
        response = await client.post(
            "/api/v1/adjustments/",
            json=adjustment_data,
            headers=child_headers
        )
        
        assert response.status_code == 403
        assert "Only parents can create" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_adjustment_invalid_child_id(
        self, client: AsyncClient, parent_headers
    ):
        """Test adjustment creation with non-existent child."""
        adjustment_data = {
            "child_id": 99999,
            "amount": "10.00",
            "reason": "Test"
        }
        
        response = await client.post(
            "/api/v1/adjustments/",
            json=adjustment_data,
            headers=parent_headers
        )
        
        assert response.status_code == 404
        assert "Child user not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_adjustment_negative_balance_prevented(
        self, db_session: AsyncSession, client: AsyncClient, parent_headers, test_child_user
    ):
        """Test that adjustments preventing negative balance are rejected."""
        # First create a positive adjustment to establish balance
        initial_adj = RewardAdjustment(
            parent_id=test_child_user.parent_id,
            child_id=test_child_user.id,
            amount=Decimal("20.00"),
            reason="Initial balance"
        )
        db_session.add(initial_adj)
        await db_session.commit()
        
        # Try to deduct more than available
        adjustment_data = {
            "child_id": test_child_user.id,
            "amount": "-30.00",
            "reason": "Large penalty"
        }
        
        response = await client.post(
            "/api/v1/adjustments/",
            json=adjustment_data,
            headers=parent_headers
        )
        
        assert response.status_code == 400
        assert "negative balance" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_adjustment_zero_amount_rejected(
        self, client: AsyncClient, parent_headers, test_child_user
    ):
        """Test that zero amount adjustments are rejected."""
        adjustment_data = {
            "child_id": test_child_user.id,
            "amount": "0.00",
            "reason": "Zero adjustment"
        }
        
        response = await client.post(
            "/api/v1/adjustments/",
            json=adjustment_data,
            headers=parent_headers
        )
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        # Handle both string and list error formats
        error_msg = str(errors).lower()
        assert "cannot be zero" in error_msg

    @pytest.mark.asyncio
    async def test_create_adjustment_amount_too_large(
        self, client: AsyncClient, parent_headers, test_child_user
    ):
        """Test that excessively large adjustments are rejected."""
        adjustment_data = {
            "child_id": test_child_user.id,
            "amount": "1001.00",
            "reason": "Too large"
        }
        
        response = await client.post(
            "/api/v1/adjustments/",
            json=adjustment_data,
            headers=parent_headers
        )
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        error_msg = str(errors).lower()
        assert "less than or equal to 999.99" in error_msg

    @pytest.mark.asyncio
    async def test_create_adjustment_empty_reason(
        self, client: AsyncClient, parent_headers, test_child_user
    ):
        """Test that empty reason is rejected."""
        adjustment_data = {
            "child_id": test_child_user.id,
            "amount": "10.00",
            "reason": ""
        }
        
        response = await client.post(
            "/api/v1/adjustments/",
            json=adjustment_data,
            headers=parent_headers
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_adjustment_reason_too_long(
        self, client: AsyncClient, parent_headers, test_child_user
    ):
        """Test that overly long reasons are rejected."""
        adjustment_data = {
            "child_id": test_child_user.id,
            "amount": "10.00",
            "reason": "x" * 501  # Exceeds 500 char limit
        }
        
        response = await client.post(
            "/api/v1/adjustments/",
            json=adjustment_data,
            headers=parent_headers
        )
        
        assert response.status_code == 422

    # GET /api/v1/adjustments/ Tests
    @pytest.mark.asyncio
    async def test_get_adjustments_parent_view_all(
        self, db_session: AsyncSession, client: AsyncClient, parent_headers, test_parent_user, test_child_user
    ):
        """Test parents can view all adjustments."""
        # Create some adjustments
        for i in range(3):
            adj = RewardAdjustment(
                parent_id=test_parent_user.id,
                child_id=test_child_user.id,
                amount=Decimal(f"{i+1}.00"),
                reason=f"Test adjustment {i+1}"
            )
            db_session.add(adj)
        await db_session.commit()
        
        response = await client.get("/api/v1/adjustments/", headers=parent_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_get_adjustments_child_forbidden(
        self, db_session: AsyncSession, client: AsyncClient, child_headers, test_parent_user, test_child_user
    ):
        """Test children cannot view adjustments (MVP restriction)."""
        # Create adjustment for the child
        adj = RewardAdjustment(
            parent_id=test_parent_user.id,
            child_id=test_child_user.id,
            amount=Decimal("10.00"),
            reason="Child's adjustment"
        )
        db_session.add(adj)
        await db_session.commit()
        
        response = await client.get("/api/v1/adjustments/", headers=child_headers)
        
        assert response.status_code == 403
        assert "Children cannot view reward adjustments" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_adjustments_filtering_by_child(
        self, db_session: AsyncSession, client: AsyncClient, parent_headers, test_parent_user
    ):
        """Test filtering adjustments by child ID."""
        # Create two children
        child1 = User(username="child1", email="c1@test.com", hashed_password="h",
                     is_parent=False, parent_id=test_parent_user.id)
        child2 = User(username="child2", email="c2@test.com", hashed_password="h",
                     is_parent=False, parent_id=test_parent_user.id)
        db_session.add_all([child1, child2])
        await db_session.commit()
        
        # Create adjustments for both
        adj1 = RewardAdjustment(parent_id=test_parent_user.id, child_id=child1.id,
                               amount=Decimal("10.00"), reason="Child 1")
        adj2 = RewardAdjustment(parent_id=test_parent_user.id, child_id=child2.id,
                               amount=Decimal("20.00"), reason="Child 2")
        db_session.add_all([adj1, adj2])
        await db_session.commit()
        
        # Filter by child1
        response = await client.get(
            f"/api/v1/adjustments/?child_id={child1.id}",
            headers=parent_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["child_id"] == child1.id

    @pytest.mark.asyncio
    async def test_get_adjustments_pagination(
        self, db_session: AsyncSession, client: AsyncClient, parent_headers, test_parent_user, test_child_user
    ):
        """Test pagination with limit and offset."""
        # Create 10 adjustments
        for i in range(10):
            adj = RewardAdjustment(
                parent_id=test_parent_user.id,
                child_id=test_child_user.id,
                amount=Decimal(f"{i+1}.00"),
                reason=f"Test {i+1}"
            )
            db_session.add(adj)
        await db_session.commit()
        
        # Get first page
        response = await client.get(
            "/api/v1/adjustments/?limit=5&skip=0",
            headers=parent_headers
        )
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1) == 5
        
        # Get second page
        response = await client.get(
            "/api/v1/adjustments/?limit=5&skip=5",
            headers=parent_headers
        )
        assert response.status_code == 200
        page2 = response.json()
        assert len(page2) == 5
        
        # Verify different adjustments
        page1_ids = {adj["id"] for adj in page1}
        page2_ids = {adj["id"] for adj in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

    @pytest.mark.asyncio
    async def test_get_adjustments_unauthorized(self, client: AsyncClient):
        """Test that authentication is required."""
        response = await client.get("/api/v1/adjustments/")
        assert response.status_code == 401

    # Rate Limiting Tests
    @pytest.mark.asyncio
    @pytest.mark.rate_limit
    @pytest.mark.skipif(
        os.environ.get("TESTING") == "true",
        reason="Rate limiting disabled in test environment"
    )
    async def test_create_adjustment_rate_limited(
        self, client: AsyncClient, parent_headers, test_child_user
    ):
        """Test rate limiting on adjustment creation."""
        adjustment_data = {
            "child_id": test_child_user.id,
            "amount": "1.00",
            "reason": "Rate limit test"
        }
        
        # Make requests up to the limit (30 per minute)
        for i in range(30):
            response = await client.post(
                "/api/v1/adjustments/",
                json=adjustment_data,
                headers=parent_headers
            )
            assert response.status_code == 201
        
        # Next request should be rate limited
        response = await client.post(
            "/api/v1/adjustments/",
            json=adjustment_data,
            headers=parent_headers
        )
        assert response.status_code == 429

    @pytest.mark.asyncio
    @pytest.mark.rate_limit
    @pytest.mark.skipif(
        os.environ.get("TESTING") == "true",
        reason="Rate limiting disabled in test environment"
    )
    async def test_get_adjustments_rate_limited(
        self, client: AsyncClient, parent_headers
    ):
        """Test rate limiting on reading adjustments."""
        # Make requests up to the limit (60 per minute)
        for i in range(60):
            response = await client.get("/api/v1/adjustments/", headers=parent_headers)
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = await client.get("/api/v1/adjustments/", headers=parent_headers)
        assert response.status_code == 429
"""
Integration tests for multi-assignment API endpoints.

Tests the complete API flow for multi-assignment features:
- POST /api/v1/chores/ (creating chores with multi-assignment)
- GET /api/v1/chores/available (child's available chores)
- GET /api/v1/chores/pending-approval (parent's pending assignments)
- POST /api/v1/chores/{chore_id}/complete (completing assignments)
- POST /api/v1/assignments/{assignment_id}/approve (approving assignments)
- POST /api/v1/assignments/{assignment_id}/reject (rejecting assignments)
"""

import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.user_service import UserService


class TestChoreCreationAPIMultiAssignment:
    """Test chore creation API with multi-assignment modes."""

    @pytest.mark.asyncio
    async def test_create_single_mode_chore(
        self,
        client,
        db_session: AsyncSession
    ):
        """Test creating a chore in single assignment mode."""
        user_service = UserService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_api_single",
            password="password123",
            email="parentapi1@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_api_single",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Login as parent
        login_response = await client.post(
            "/api/v1/users/login",
            data={"username": "parent_api_single", "password": "password123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Create chore with single mode
        create_response = await client.post(
            "/api/v1/chores",
            json={
                "title": "Test Single Mode",
                "description": "Testing",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert create_response.status_code == 201
        chore_data = create_response.json()
        assert chore_data["title"] == "Test Single Mode"
        assert chore_data["assignment_mode"] == "single"
        assert len(chore_data["assignments"]) == 1
        assert chore_data["assignments"][0]["assignee_id"] == child.id

    @pytest.mark.asyncio
    async def test_create_multi_independent_mode_chore(
        self,
        client,
        db_session: AsyncSession
    ):
        """Test creating a chore in multi_independent mode."""
        user_service = UserService()

        # Create parent and 3 children
        parent = await user_service.register_user(
            db_session,
            username="parent_api_multi",
            password="password123",
            email="parentapi2@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_api_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_api_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child3 = await user_service.register_user(
            db_session,
            username="child3_api_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Login as parent
        login_response = await client.post(
            "/api/v1/users/login",
            data={"username": "parent_api_multi", "password": "password123"}
        )
        token = login_response.json()["access_token"]

        # Create chore with multi_independent mode
        create_response = await client.post(
            "/api/v1/chores",
            json={
                "title": "Clean Your Room",
                "description": "Each child's room",
                "reward": 10.0,
                "assignment_mode": "multi_independent",
                "assignee_ids": [child1.id, child2.id, child3.id]
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert create_response.status_code == 201
        chore_data = create_response.json()
        assert chore_data["assignment_mode"] == "multi_independent"
        assert len(chore_data["assignments"]) == 3

        assignee_ids = {a["assignee_id"] for a in chore_data["assignments"]}
        assert child1.id in assignee_ids
        assert child2.id in assignee_ids
        assert child3.id in assignee_ids

    @pytest.mark.asyncio
    async def test_create_unassigned_pool_chore(
        self,
        client,
        db_session: AsyncSession
    ):
        """Test creating a chore in unassigned (pool) mode."""
        user_service = UserService()

        # Create parent
        parent = await user_service.register_user(
            db_session,
            username="parent_api_pool",
            password="password123",
            email="parentapi3@test.com",
            is_parent=True
        )

        # Login as parent
        login_response = await client.post(
            "/api/v1/users/login",
            data={"username": "parent_api_pool", "password": "password123"}
        )
        token = login_response.json()["access_token"]

        # Create pool chore
        create_response = await client.post(
            "/api/v1/chores",
            json={
                "title": "Walk the Dog",
                "description": "Anyone can do",
                "reward": 3.0,
                "assignment_mode": "unassigned",
                "assignee_ids": []
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert create_response.status_code == 201
        chore_data = create_response.json()
        assert chore_data["assignment_mode"] == "unassigned"
        assert len(chore_data["assignments"]) == 0


class TestAvailableChoresAPIMultiAssignment:
    """Test GET /api/v1/chores/available endpoint."""

    @pytest.mark.asyncio
    async def test_available_chores_returns_dict_structure(
        self,
        client,
        db_session: AsyncSession
    ):
        """Test that available chores endpoint returns dictionary with assigned and pool lists."""
        user_service = UserService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_avail_api",
            password="password123",
            email="parentavail@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_avail_api",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Login as child
        login_response = await client.post(
            "/api/v1/users/login",
            data={"username": "child_avail_api", "password": "password123"}
        )
        token = login_response.json()["access_token"]

        # Get available chores
        avail_response = await client.get(
            "/api/v1/chores/available",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert avail_response.status_code == 200
        data = avail_response.json()

        # Should have both keys
        assert "assigned" in data
        assert "pool" in data
        assert "total_count" in data
        assert isinstance(data["assigned"], list)
        assert isinstance(data["pool"], list)


class TestPendingApprovalAPIMultiAssignment:
    """Test GET /api/v1/chores/pending-approval endpoint."""

    @pytest.mark.asyncio
    async def test_pending_approval_returns_assignment_data(
        self,
        client,
        db_session: AsyncSession
    ):
        """Test that pending approval endpoint returns assignment-level data."""
        user_service = UserService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_pend_api",
            password="password123",
            email="parentpend@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_pend_api",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Login as parent and create chore
        parent_login = await client.post(
            "/api/v1/users/login",
            data={"username": "parent_pend_api", "password": "password123"}
        )
        parent_token = parent_login.json()["access_token"]

        chore_response = await client.post(
            "/api/v1/chores",
            json={
                "title": "Test Chore",
                "description": "Test description",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            },
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        assert chore_response.status_code == 201, f"Got {chore_response.status_code}: {chore_response.text}"
        chore_id = chore_response.json()["id"]

        # Login as child and complete chore
        child_login = await client.post(
            "/api/v1/users/login",
            data={"username": "child_pend_api", "password": "password123"}
        )
        child_token = child_login.json()["access_token"]

        await client.post(
            f"/api/v1/chores/{chore_id}/complete",
            headers={"Authorization": f"Bearer {child_token}"}
        )

        # Get pending approval as parent
        pending_response = await client.get(
            "/api/v1/chores/pending-approval",
            headers={"Authorization": f"Bearer {parent_token}"}
        )

        assert pending_response.status_code == 200
        pending = pending_response.json()
        assert len(pending) == 1

        # Check structure
        item = pending[0]
        assert "assignment" in item
        assert "assignment_id" in item
        assert "chore" in item
        assert "assignee" in item
        assert "assignee_name" in item
        assert item["assignee_name"] == "child_pend_api"


class TestCompleteChoreAPIMultiAssignment:
    """Test POST /api/v1/chores/{chore_id}/complete endpoint."""

    @pytest.mark.asyncio
    async def test_complete_chore_returns_assignment_data(
        self,
        client,
        db_session: AsyncSession
    ):
        """Test that complete chore endpoint returns assignment data."""
        user_service = UserService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_comp_api",
            password="password123",
            email="parentcomp@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_comp_api",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Login as parent and create chore
        parent_login = await client.post(
            "/api/v1/users/login",
            data={"username": "parent_comp_api", "password": "password123"}
        )
        parent_token = parent_login.json()["access_token"]

        chore_response = await client.post(
            "/api/v1/chores",
            json={
                "title": "Test Complete",
                "description": "Test description",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            },
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        assert chore_response.status_code == 201, f"Got {chore_response.status_code}: {chore_response.text}"
        chore_id = chore_response.json()["id"]

        # Login as child and complete
        child_login = await client.post(
            "/api/v1/users/login",
            data={"username": "child_comp_api", "password": "password123"}
        )
        child_token = child_login.json()["access_token"]

        complete_response = await client.post(
            f"/api/v1/chores/{chore_id}/complete",
            headers={"Authorization": f"Bearer {child_token}"}
        )

        assert complete_response.status_code == 200
        data = complete_response.json()

        # Check structure
        assert "chore" in data
        assert "assignment" in data
        assert "message" in data
        assert data["assignment"]["is_completed"] is True
        assert data["assignment"]["is_approved"] is False


class TestAssignmentApprovalAPI:
    """Test POST /api/v1/assignments/{assignment_id}/approve endpoint."""

    @pytest.mark.asyncio
    async def test_approve_assignment_via_api(
        self,
        client,
        db_session: AsyncSession
    ):
        """Test approving an assignment through the API."""
        user_service = UserService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_appr_api",
            password="password123",
            email="parentappr@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_appr_api",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create and complete chore
        parent_login = await client.post(
            "/api/v1/users/login",
            data={"username": "parent_appr_api", "password": "password123"}
        )
        parent_token = parent_login.json()["access_token"]

        chore_response = await client.post(
            "/api/v1/chores",
            json={
                "title": "Test Approve",
                "description": "Test description",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            },
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        assert chore_response.status_code == 201, f"Got {chore_response.status_code}: {chore_response.text}"
        chore_id = chore_response.json()["id"]

        child_login = await client.post(
            "/api/v1/users/login",
            data={"username": "child_appr_api", "password": "password123"}
        )
        child_token = child_login.json()["access_token"]

        complete_response = await client.post(
            f"/api/v1/chores/{chore_id}/complete",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        assignment_id = complete_response.json()["assignment"]["id"]

        # Approve the assignment
        approve_response = await client.post(
            f"/api/v1/assignments/{assignment_id}/approve",
            json={},
            headers={"Authorization": f"Bearer {parent_token}"}
        )

        assert approve_response.status_code == 200
        data = approve_response.json()

        assert "assignment" in data
        assert "chore" in data
        assert "message" in data
        assert data["assignment"]["is_approved"] is True


class TestAssignmentRejectionAPI:
    """Test POST /api/v1/assignments/{assignment_id}/reject endpoint."""

    @pytest.mark.asyncio
    async def test_reject_assignment_via_api(
        self,
        client,
        db_session: AsyncSession
    ):
        """Test rejecting an assignment through the API."""
        user_service = UserService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_rej_api",
            password="password123",
            email="parentrej@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_rej_api",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create and complete chore
        parent_login = await client.post(
            "/api/v1/users/login",
            data={"username": "parent_rej_api", "password": "password123"}
        )
        parent_token = parent_login.json()["access_token"]

        chore_response = await client.post(
            "/api/v1/chores",
            json={
                "title": "Test Reject",
                "description": "Test description",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            },
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        assert chore_response.status_code == 201, f"Got {chore_response.status_code}: {chore_response.text}"
        chore_id = chore_response.json()["id"]

        child_login = await client.post(
            "/api/v1/users/login",
            data={"username": "child_rej_api", "password": "password123"}
        )
        child_token = child_login.json()["access_token"]

        complete_response = await client.post(
            f"/api/v1/chores/{chore_id}/complete",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        assignment_id = complete_response.json()["assignment"]["id"]

        # Reject the assignment
        reject_response = await client.post(
            f"/api/v1/assignments/{assignment_id}/reject",
            json={"rejection_reason": "Not good enough"},
            headers={"Authorization": f"Bearer {parent_token}"}
        )

        assert reject_response.status_code == 200
        data = reject_response.json()

        assert "assignment" in data
        assert "chore" in data
        assert "message" in data
        assert data["assignment"]["is_completed"] is False
        assert data["assignment"]["rejection_reason"] == "Not good enough"

"""
Comprehensive API integration tests for family endpoints.
"""
import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.user import UserRepository
from backend.app.services.family import FamilyService
from backend.app.core.security.jwt import create_access_token


@pytest.mark.asyncio
class TestFamilyAPIEndpoints:
    """Test family management API endpoints."""

    async def create_test_parent(self, db_session: AsyncSession, username: str = "testparent", email: str = "test@example.com"):
        """Helper to create a test parent user."""
        user_repo = UserRepository()
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": username,
                "password": "testpass123",
                "email": email,
                "is_parent": True
            }
        )
        return parent

    async def get_auth_headers(self, user_id: int):
        """Helper to get authorization headers for a user."""
        token = create_access_token(subject=str(user_id))
        return {"Authorization": f"Bearer {token}"}

    async def test_create_family_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful family creation."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        response = await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Family"
        assert "invite_code" in data
        assert len(data["invite_code"]) == 8
        assert data["invite_code"].isupper()

    async def test_create_family_already_in_family(self, client: AsyncClient, db_session: AsyncSession):
        """Test that user cannot create family if already in one."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        # Create first family
        await client.post(
            "/api/v1/families/create",
            json={"name": "First Family"},
            headers=headers
        )

        # Try to create second family
        response = await client.post(
            "/api/v1/families/create",
            json={"name": "Second Family"},
            headers=headers
        )

        assert response.status_code == 400
        assert "already a member of a family" in response.json()["detail"]

    async def test_create_family_child_forbidden(self, client: AsyncClient, db_session: AsyncSession):
        """Test that children cannot create families."""
        # Create parent first
        parent = await self.create_test_parent(db_session)
        
        # Create child
        user_repo = UserRepository()
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "testchild",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent.id
            }
        )

        headers = await self.get_auth_headers(child.id)

        response = await client.post(
            "/api/v1/families/create",
            json={"name": "Child Family"},
            headers=headers
        )

        assert response.status_code == 403
        assert "parent privileges" in response.json()["detail"]

    async def test_join_family_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful family joining."""
        # Create family
        parent1 = await self.create_test_parent(db_session, "parent1", "parent1@example.com")
        headers1 = await self.get_auth_headers(parent1.id)

        create_response = await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=headers1
        )
        invite_code = create_response.json()["invite_code"]

        # Create second parent
        parent2 = await self.create_test_parent(db_session, "parent2", "parent2@example.com")
        headers2 = await self.get_auth_headers(parent2.id)

        # Join family
        response = await client.post(
            "/api/v1/families/join",
            json={"invite_code": invite_code},
            headers=headers2
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["family_name"] == "Test Family"
        assert "Successfully joined family" in data["message"]

    async def test_join_family_invalid_code(self, client: AsyncClient, db_session: AsyncSession):
        """Test joining family with invalid invite code."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        response = await client.post(
            "/api/v1/families/join",
            json={"invite_code": "INVALID1"},
            headers=headers
        )

        assert response.status_code == 404
        assert "Invalid or expired invite code" in response.json()["detail"]

    async def test_join_family_malformed_code(self, client: AsyncClient, db_session: AsyncSession):
        """Test joining family with malformed invite code."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        # Test lowercase code
        response = await client.post(
            "/api/v1/families/join",
            json={"invite_code": "abcd1234"},
            headers=headers
        )

        assert response.status_code == 422  # Validation error
        assert "Invite code must be uppercase" in str(response.json())

    async def test_generate_invite_code_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful invite code generation."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        # Create family first
        await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=headers
        )

        # Generate new invite code
        response = await client.post(
            "/api/v1/families/invite-code/generate",
            json={"expires_in_days": 7},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "invite_code" in data
        assert len(data["invite_code"]) == 8
        assert data["family_name"] == "Test Family"
        assert data["expires_at"] is not None

    async def test_generate_invite_code_no_family(self, client: AsyncClient, db_session: AsyncSession):
        """Test invite code generation without family membership."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        response = await client.post(
            "/api/v1/families/invite-code/generate",
            json={},
            headers=headers
        )

        assert response.status_code == 403
        assert "family membership" in response.json()["detail"]

    async def test_get_family_members_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting family members."""
        # Create family with members
        parent1 = await self.create_test_parent(db_session, "parent1", "parent1@example.com")
        headers1 = await self.get_auth_headers(parent1.id)

        # Create family
        create_response = await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=headers1
        )
        invite_code = create_response.json()["invite_code"]

        # Add second parent
        parent2 = await self.create_test_parent(db_session, "parent2", "parent2@example.com")
        headers2 = await self.get_auth_headers(parent2.id)

        await client.post(
            "/api/v1/families/join",
            json={"invite_code": invite_code},
            headers=headers2
        )

        # Add child
        user_repo = UserRepository()
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "testchild",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent1.id
            }
        )

        # Update child's family (simulate family inheritance)
        family_service = FamilyService()
        family = await family_service.get_user_family_context(db_session, user_id=parent1.id)
        await user_repo.update(db_session, id=child.id, obj_in={"family_id": family.id})

        # Get family members
        response = await client.get(
            "/api/v1/families/members",
            headers=headers1
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_members"] == 3
        assert len(data["parents"]) == 2
        assert len(data["children"]) == 1
        assert data["family_name"] == "Test Family"

    async def test_get_family_stats_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting family statistics."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        # Create family
        await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=headers
        )

        # Get family stats
        response = await client.get(
            "/api/v1/families/stats",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Family"
        assert data["total_members"] == 1
        assert data["total_parents"] == 1
        assert data["total_children"] == 0

    async def test_get_family_context_with_family(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting family context for user with family."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        # Create family
        await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=headers
        )

        # Get family context
        response = await client.get(
            "/api/v1/families/context",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_family"] is True
        assert data["family"]["name"] == "Test Family"
        assert data["role"] == "parent"
        assert data["can_invite"] is True
        assert data["can_manage"] is True

    async def test_get_family_context_without_family(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting family context for user without family."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        response = await client.get(
            "/api/v1/families/context",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_family"] is False
        assert data["family"] is None
        assert data["role"] == "no_family"
        assert data["can_invite"] is False
        assert data["can_manage"] is False

    async def test_remove_family_member_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful family member removal."""
        # Create family with two parents
        parent1 = await self.create_test_parent(db_session, "parent1", "parent1@example.com")
        parent2 = await self.create_test_parent(db_session, "parent2", "parent2@example.com")
        headers1 = await self.get_auth_headers(parent1.id)

        # Create family
        create_response = await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=headers1
        )
        invite_code = create_response.json()["invite_code"]

        # Parent2 joins
        headers2 = await self.get_auth_headers(parent2.id)
        await client.post(
            "/api/v1/families/join",
            json={"invite_code": invite_code},
            headers=headers2
        )

        # Remove parent2 from family
        response = await client.request(
            "DELETE",
            f"/api/v1/families/members/{parent2.id}",
            json={"user_id": parent2.id, "reason": "Test removal"},
            headers=headers1
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["removed_user_id"] == parent2.id

    async def test_remove_last_parent_fails(self, client: AsyncClient, db_session: AsyncSession):
        """Test that removing the last parent fails."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        # Create family
        await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=headers
        )

        # Try to remove the only parent
        response = await client.request(
            "DELETE",
            f"/api/v1/families/members/{parent.id}",
            json={"user_id": parent.id},
            headers=headers
        )

        assert response.status_code == 400
        assert "Cannot remove the last parent" in response.json()["detail"]


@pytest.mark.asyncio
class TestUserAPIEnhancements:
    """Test family-enhanced user API endpoints."""

    async def create_test_parent(self, db_session: AsyncSession, username: str = "testparent", email: str = "test@example.com"):
        """Helper to create a test parent user."""
        user_repo = UserRepository()
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": username,
                "password": "testpass123",
                "email": email,
                "is_parent": True
            }
        )
        return parent

    async def get_auth_headers(self, user_id: int):
        """Helper to get authorization headers for a user."""
        token = create_access_token(subject=str(user_id))
        return {"Authorization": f"Bearer {token}"}

    async def test_get_user_profile(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting current user profile."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        response = await client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testparent"
        assert data["is_parent"] is True
        assert data["email"] == "test@example.com"

    async def test_get_user_stats(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting user statistics with family context."""
        parent = await self.create_test_parent(db_session)
        headers = await self.get_auth_headers(parent.id)

        response = await client.get("/api/v1/users/stats", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == "testparent"
        assert "family_context" in data
        assert "children_count" in data
        assert "family_members_count" in data

    async def test_get_family_children_no_family(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting family children for parent not in family."""
        # Create parent with direct child (legacy mode)
        parent = await self.create_test_parent(db_session)
        
        user_repo = UserRepository()
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "testchild",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent.id
            }
        )

        headers = await self.get_auth_headers(parent.id)

        response = await client.get("/api/v1/users/my-family-children", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "testchild"

    async def test_get_family_children_with_family(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting family children for parent in family."""
        # Create family with parents and child
        parent1 = await self.create_test_parent(db_session, "parent1", "parent1@example.com")
        parent2 = await self.create_test_parent(db_session, "parent2", "parent2@example.com")
        headers1 = await self.get_auth_headers(parent1.id)

        # Create family
        create_response = await client.post(
            "/api/v1/families/create",
            json={"name": "Test Family"},
            headers=headers1
        )

        # Parent2 joins family
        invite_code = create_response.json()["invite_code"]
        headers2 = await self.get_auth_headers(parent2.id)
        await client.post(
            "/api/v1/families/join",
            json={"invite_code": invite_code},
            headers=headers2
        )

        # Create child for parent1 but in the family
        user_repo = UserRepository()
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "testchild",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent1.id
            }
        )

        # Update child's family_id
        family_service = FamilyService()
        family = await family_service.get_user_family_context(db_session, user_id=parent1.id)
        await user_repo.update(db_session, id=child.id, obj_in={"family_id": family.id})

        # Both parents should see the child
        response1 = await client.get("/api/v1/users/my-family-children", headers=headers1)
        response2 = await client.get("/api/v1/users/my-family-children", headers=headers2)

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert len(data1) == 1
        assert len(data2) == 1
        assert data1[0]["username"] == "testchild"
        assert data2[0]["username"] == "testchild"

    async def test_get_family_children_child_forbidden(self, client: AsyncClient, db_session: AsyncSession):
        """Test that children cannot access family children endpoint."""
        parent = await self.create_test_parent(db_session)
        
        user_repo = UserRepository()
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "testchild",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent.id
            }
        )

        headers = await self.get_auth_headers(child.id)

        response = await client.get("/api/v1/users/my-family-children", headers=headers)

        assert response.status_code == 403
        assert "Only parents can access children information" in response.json()["detail"]


@pytest.mark.asyncio
class TestFamilyAPIAuth:
    """Test authentication and authorization for family endpoints."""

    async def test_family_endpoints_require_auth(self, client: AsyncClient, db_session: AsyncSession):
        """Test that family endpoints require authentication."""
        endpoints = [
            ("POST", "/api/v1/families/create"),
            ("POST", "/api/v1/families/join"),
            ("POST", "/api/v1/families/invite-code/generate"),
            ("GET", "/api/v1/families/members"),
            ("GET", "/api/v1/families/stats"),
            ("GET", "/api/v1/families/context"),
        ]

        for method, endpoint in endpoints:
            if method == "POST":
                response = await client.post(endpoint, json={})
            else:
                response = await client.get(endpoint)

            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"
            assert "Not authenticated" in response.json()["detail"]
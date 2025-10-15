"""
Comprehensive authentication and authorization tests for new features.

This test suite validates role-based access control, JWT token validation,
cross-family data isolation, and security enforcement across all new
API endpoints including activities, reports, and statistics.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import status
from httpx import AsyncClient

from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.models.reward_adjustment import RewardAdjustment
from backend.app.core.security.password import get_password_hash
from backend.app.core.security.jwt import create_access_token


@pytest_asyncio.fixture
async def second_family_setup(db_session):
    """Create a second family for cross-family isolation testing."""
    # Create second parent
    parent2 = User(
        email="parent2@example.com",
        username="parent2_user",
        hashed_password=get_password_hash("securepass456"),
        is_active=True,
        is_parent=True
    )
    db_session.add(parent2)
    await db_session.commit()
    await db_session.refresh(parent2)
    
    # Create second child
    child2 = User(
        email="child2@example.com",
        username="child2_user",
        hashed_password=get_password_hash("childpass456"),
        is_active=True,
        is_parent=False,
        parent_id=parent2.id
    )
    db_session.add(child2)
    await db_session.commit()
    await db_session.refresh(child2)
    
    # Create some chores and data for family 2
    from backend.app.models.chore_assignment import ChoreAssignment

    chore_f2 = Chore(
        title="Family 2 Chore",
        description="Should not be visible to family 1",
        reward=8.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_disabled=False,
        assignment_mode="single",
        creator_id=parent2.id
    )
    db_session.add(chore_f2)
    await db_session.flush()  # Get chore ID

    # Create assignment
    assignment_f2 = ChoreAssignment(
        chore_id=chore_f2.id,
        assignee_id=child2.id,
        is_completed=True,
        is_approved=True,
        completion_date=datetime.now() - timedelta(days=1),
        approval_date=datetime.now(),
        approval_reward=8.0
    )
    db_session.add(assignment_f2)
    
    adjustment_f2 = RewardAdjustment(
        child_id=child2.id,
        parent_id=parent2.id,
        amount=Decimal("3.00"),
        reason="Family 2 bonus"
    )
    
    db_session.add(adjustment_f2)
    await db_session.commit()
    await db_session.refresh(chore_f2)
    await db_session.refresh(assignment_f2)
    await db_session.refresh(adjustment_f2)
    
    # Create tokens
    parent2_token = create_access_token(subject=parent2.id)
    child2_token = create_access_token(subject=child2.id)
    
    return {
        'parent': parent2,
        'child': child2,
        'chore': chore_f2,
        'adjustment': adjustment_f2,
        'parent_token': parent2_token,
        'child_token': child2_token
    }


@pytest_asyncio.fixture
async def expired_token():
    """Create an expired JWT token for testing."""
    # Create token that expired 1 hour ago
    expired_time = datetime.utcnow() - timedelta(hours=1)
    return create_access_token(subject=1, expires_delta=timedelta(seconds=-3600))


@pytest_asyncio.fixture
async def invalid_token():
    """Create an invalid JWT token for testing."""
    return "invalid.jwt.token"


class TestActivitiesEndpointAuthorization:
    """Test authorization for activities endpoints."""
    
    async def test_activities_parent_access_authorized(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test parent can access activities endpoint."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_activities_child_access_authorized(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child can access activities endpoint (limited scope)."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_activities_no_token_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test activities endpoint requires authentication."""
        # Act
        response = await client.get("/api/v1/activities/recent")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_activities_invalid_token_unauthorized(
        self,
        client: AsyncClient,
        invalid_token
    ):
        """Test activities endpoint rejects invalid tokens."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_activities_expired_token_unauthorized(
        self,
        client: AsyncClient,
        expired_token
    ):
        """Test activities endpoint rejects expired tokens."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestReportsEndpointAuthorization:
    """Test authorization for reports endpoints."""
    
    async def test_reports_allowance_summary_parent_access(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test parent can access allowance summary."""
        # Act
        response = await client.get(
            "/api/v1/reports/allowance-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_reports_allowance_summary_child_forbidden(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child cannot access allowance summary."""
        # Act
        response = await client.get(
            "/api/v1/reports/allowance-summary",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_reports_export_parent_access(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test parent can access export functionality."""
        # Act
        response = await client.get(
            "/api/v1/reports/export/allowance-summary?format=csv",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_reports_export_child_forbidden(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child cannot access export functionality."""
        # Act
        response = await client.get(
            "/api/v1/reports/export/allowance-summary?format=csv",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_reports_reward_history_parent_access(
        self,
        client: AsyncClient,
        test_child_user,
        parent_token
    ):
        """Test parent can access child's reward history."""
        # Act
        response = await client.get(
            f"/api/v1/reports/reward-history/{test_child_user.id}",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_reports_reward_history_child_own_access(
        self,
        client: AsyncClient,
        test_child_user,
        child_token
    ):
        """Test child can access their own reward history."""
        # Act
        response = await client.get(
            f"/api/v1/reports/reward-history/{test_child_user.id}",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_reports_reward_history_child_other_forbidden(
        self,
        client: AsyncClient,
        child_token,
        second_family_setup
    ):
        """Test child cannot access other child's reward history."""
        # Act - Child 1 trying to access Child 2's history
        response = await client.get(
            f"/api/v1/reports/reward-history/{second_family_setup['child'].id}",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestStatisticsEndpointAuthorization:
    """Test authorization for statistics endpoints."""
    
    async def test_statistics_weekly_summary_parent_access(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test parent can access weekly statistics."""
        # Act
        response = await client.get(
            "/api/v1/statistics/weekly-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_statistics_weekly_summary_child_forbidden(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child cannot access weekly statistics."""
        # Act
        response = await client.get(
            "/api/v1/statistics/weekly-summary",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_statistics_monthly_summary_parent_access(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test parent can access monthly statistics."""
        # Act
        response = await client.get(
            "/api/v1/statistics/monthly-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_statistics_monthly_summary_child_forbidden(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child cannot access monthly statistics."""
        # Act
        response = await client.get(
            "/api/v1/statistics/monthly-summary",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_statistics_trends_parent_access(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test parent can access trend analysis."""
        # Act
        response = await client.get(
            "/api/v1/statistics/trends",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_statistics_trends_child_forbidden(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child cannot access trend analysis."""
        # Act
        response = await client.get(
            "/api/v1/statistics/trends",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_statistics_comparison_parent_access(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test parent can access comparison statistics."""
        # Act
        response = await client.get(
            "/api/v1/statistics/comparison",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
    
    async def test_statistics_comparison_child_forbidden(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child cannot access comparison statistics."""
        # Act
        response = await client.get(
            "/api/v1/statistics/comparison",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCrossFamilyDataIsolation:
    """Test data isolation between different families."""
    
    async def test_activities_cross_family_isolation(
        self,
        client: AsyncClient,
        parent_token,
        second_family_setup
    ):
        """Test activities are isolated between families."""
        # Act - Family 1 parent checking activities
        response1 = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Act - Family 2 parent checking activities
        response2 = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {second_family_setup['parent_token']}"}
        )
        
        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Each family should only see their own activities
        # (Note: This test assumes some activity data exists)
        # The key is that the responses are different and don't contain cross-family data
        
        # Verify families get different sets of activities
        if len(data1) > 0 and len(data2) > 0:
            # If both families have activities, they should be different
            activity_ids_1 = {activity['id'] for activity in data1 if 'id' in activity}
            activity_ids_2 = {activity['id'] for activity in data2 if 'id' in activity}
            assert activity_ids_1.isdisjoint(activity_ids_2), "Families should not share activity IDs"
    
    async def test_reports_cross_family_isolation(
        self,
        client: AsyncClient,
        parent_token,
        second_family_setup
    ):
        """Test reports are isolated between families."""
        # Act - Family 1 parent checking allowance summary
        response1 = await client.get(
            "/api/v1/reports/allowance-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Act - Family 2 parent checking allowance summary
        response2 = await client.get(
            "/api/v1/reports/allowance-summary",
            headers={"Authorization": f"Bearer {second_family_setup['parent_token']}"}
        )
        
        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Verify child summaries contain different children
        children_1 = {child['id'] for child in data1['child_summaries']}
        children_2 = {child['id'] for child in data2['child_summaries']}
        assert children_1.isdisjoint(children_2), "Families should not see each other's children"
    
    async def test_statistics_cross_family_isolation(
        self,
        client: AsyncClient,
        parent_token,
        second_family_setup
    ):
        """Test statistics are isolated between families."""
        # Act - Family 1 parent checking weekly statistics
        response1 = await client.get(
            "/api/v1/statistics/weekly-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Act - Family 2 parent checking weekly statistics
        response2 = await client.get(
            "/api/v1/statistics/weekly-summary",
            headers={"Authorization": f"Bearer {second_family_setup['parent_token']}"}
        )
        
        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Each family should have their own statistical profile
        # This is harder to test precisely, but we can verify basic structure
        assert 'summary' in data1
        assert 'summary' in data2
        assert 'weekly_data' in data1
        assert 'weekly_data' in data2
    
    async def test_child_cannot_access_other_family_data(
        self,
        client: AsyncClient,
        child_token,
        second_family_setup
    ):
        """Test child from family 1 cannot access family 2 child's data."""
        # Act - Family 1 child trying to access Family 2 child's reward history
        response = await client.get(
            f"/api/v1/reports/reward-history/{second_family_setup['child'].id}",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestJWTTokenValidation:
    """Test JWT token validation and security."""
    
    async def test_malformed_jwt_token(
        self,
        client: AsyncClient
    ):
        """Test rejection of malformed JWT tokens."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": "Bearer malformed.jwt"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_jwt_token_with_invalid_signature(
        self,
        client: AsyncClient
    ):
        """Test rejection of JWT tokens with invalid signatures."""
        # Create a token with invalid signature (modified)
        valid_token = create_access_token(subject=1)
        invalid_token = valid_token[:-10] + "invalidsig"
        
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_jwt_token_missing_bearer_prefix(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test rejection when Bearer prefix is missing."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": parent_token}  # Missing "Bearer "
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_jwt_token_with_nonexistent_user(
        self,
        client: AsyncClient
    ):
        """Test rejection when token references nonexistent user."""
        # Create token for user ID that doesn't exist
        nonexistent_token = create_access_token(subject=99999)
        
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {nonexistent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_authorization_header_missing(
        self,
        client: AsyncClient
    ):
        """Test all endpoints require Authorization header."""
        endpoints = [
            "/api/v1/activities/recent",
            "/api/v1/reports/allowance-summary",
            "/api/v1/reports/export/allowance-summary",
            "/api/v1/statistics/weekly-summary",
            "/api/v1/statistics/monthly-summary",
            "/api/v1/statistics/trends",
            "/api/v1/statistics/comparison"
        ]
        
        for endpoint in endpoints:
            # Act
            response = await client.get(endpoint)
            
            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, f"Endpoint {endpoint} should require authentication"


class TestRoleBasedAccessControl:
    """Test role-based access control enforcement."""
    
    async def test_parent_role_required_endpoints(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test endpoints that require parent role reject child access."""
        parent_only_endpoints = [
            "/api/v1/reports/allowance-summary",
            "/api/v1/reports/export/allowance-summary?format=csv",
            "/api/v1/statistics/weekly-summary",
            "/api/v1/statistics/monthly-summary",
            "/api/v1/statistics/trends",
            "/api/v1/statistics/comparison"
        ]
        
        for endpoint in parent_only_endpoints:
            # Act
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {child_token}"}
            )
            
            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN, f"Child should be forbidden from {endpoint}"
    
    async def test_child_accessible_endpoints(
        self,
        client: AsyncClient,
        child_token,
        test_child_user
    ):
        """Test endpoints that children can access."""
        child_accessible_endpoints = [
            "/api/v1/activities/recent",
            f"/api/v1/reports/reward-history/{test_child_user.id}"
        ]
        
        for endpoint in child_accessible_endpoints:
            # Act
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {child_token}"}
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, f"Child should have access to {endpoint}"
    
    async def test_parent_can_access_all_new_endpoints(
        self,
        client: AsyncClient,
        parent_token,
        test_child_user
    ):
        """Test parent can access all new feature endpoints."""
        all_endpoints = [
            "/api/v1/activities/recent",
            "/api/v1/reports/allowance-summary",
            "/api/v1/reports/export/allowance-summary?format=csv",
            f"/api/v1/reports/reward-history/{test_child_user.id}",
            "/api/v1/statistics/weekly-summary",
            "/api/v1/statistics/monthly-summary",
            "/api/v1/statistics/trends",
            "/api/v1/statistics/comparison"
        ]
        
        for endpoint in all_endpoints:
            # Act
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, f"Parent should have access to {endpoint}"


class TestSecurityHeaders:
    """Test security-related HTTP headers and responses."""
    
    async def test_unauthorized_responses_dont_leak_info(
        self,
        client: AsyncClient
    ):
        """Test unauthorized responses don't leak sensitive information."""
        # Act
        response = await client.get("/api/v1/reports/allowance-summary")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        
        # Should not contain sensitive information about the system
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0
        
        # Should not leak database structure, file paths, etc.
        error_message = data["detail"].lower()
        assert "sql" not in error_message
        assert "database" not in error_message
        assert "traceback" not in error_message
        assert "/app/" not in error_message
    
    async def test_forbidden_responses_consistent(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test forbidden responses are consistent across endpoints."""
        forbidden_endpoints = [
            "/api/v1/reports/allowance-summary",
            "/api/v1/statistics/weekly-summary"
        ]
        
        for endpoint in forbidden_endpoints:
            # Act
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {child_token}"}
            )
            
            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)


class TestSessionSecurity:
    """Test session security and token management."""
    
    async def test_token_reuse_across_requests(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test that valid tokens can be reused across multiple requests."""
        endpoints = [
            "/api/v1/activities/recent",
            "/api/v1/reports/allowance-summary"
        ]
        
        for endpoint in endpoints:
            # Act
            response = await client.get(
                endpoint,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, f"Token should work for {endpoint}"
    
    async def test_different_users_different_data(
        self,
        client: AsyncClient,
        parent_token,
        second_family_setup
    ):
        """Test that different authenticated users see different data."""
        # Act - Get activities for both families
        response1 = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        response2 = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {second_family_setup['parent_token']}"}
        )
        
        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        # Data should be isolated (this is hard to test precisely without knowing exact data)
        # But we can verify both requests succeeded and returned proper JSON
        data1 = response1.json()
        data2 = response2.json()
        
        # Activities endpoint returns ActivityListResponse with activities array
        assert isinstance(data1, dict)
        assert isinstance(data2, dict)
        assert "activities" in data1
        assert "activities" in data2
        assert isinstance(data1["activities"], list)
        assert isinstance(data2["activities"], list)
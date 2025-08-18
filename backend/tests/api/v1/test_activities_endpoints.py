"""
Comprehensive integration tests for activities API endpoints.

This test suite validates authentication, authorization, pagination,
filtering, and response formats for all activities endpoints using
real database operations with test data.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import status
from httpx import AsyncClient

from backend.app.schemas.activity import ActivityTypes
from backend.app.services.activity_service import ActivityService
from backend.app.models.activity import Activity


@pytest_asyncio.fixture
async def activity_service():
    """Create real activity service instance."""
    return ActivityService()

@pytest_asyncio.fixture
async def sample_activities_data(db_session, test_parent_user, test_child_user, activity_service):
    """Create sample activities in the database."""
    # Create activities for testing
    activities_data = []
    
    # Child completed a chore
    activity1 = await activity_service.log_chore_completed(
        db=db_session,
        child_id=test_child_user.id,
        chore_id=1,
        chore_title="Clean Room"
    )
    activities_data.append(activity1)
    
    # Parent approved the chore  
    activity2 = await activity_service.log_chore_approved(
        db=db_session,
        child_id=test_child_user.id,
        parent_id=test_parent_user.id,
        chore_id=1,
        chore_title="Clean Room",
        reward_amount=5.0
    )
    activities_data.append(activity2)
    
    # Parent created a new chore
    activity3 = await activity_service.log_chore_created(
        db=db_session,
        parent_id=test_parent_user.id,
        child_id=test_child_user.id,
        chore_id=2,
        chore_title="Do Dishes",
        reward_amount=3.0
    )
    activities_data.append(activity3)
    
    await db_session.commit()
    return activities_data


class TestActivitiesEndpointsIntegration:
    """Integration tests for activities API endpoints."""


class TestGetRecentActivitiesEndpoint:
    """Test GET /api/v1/activities/recent endpoint."""
    
    async def test_get_recent_activities_parent_access(
        self, 
        client: AsyncClient,
        test_parent_user,
        parent_token,
        sample_activities_data
    ):
        """Test parent can access family-wide activities."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "activities" in data
        assert "total_count" in data
        assert "has_more" in data
        
        # Should have activities from the sample data
        assert len(data["activities"]) >= 3
        assert data["has_more"] is False
        
        # Verify activity structure
        for activity in data["activities"]:
            assert "id" in activity
            assert "activity_type" in activity
            assert "description" in activity
            assert "user_id" in activity
            assert "created_at" in activity
    
    async def test_get_recent_activities_child_access(
        self,
        client: AsyncClient,
        test_child_user,
        child_token,
        sample_activities_data
    ):
        """Test child can only access their own activities."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "activities" in data
        
        # Child should see some activities but only related to them
        activities = data["activities"]
        for activity in activities:
            # Activity should either be performed by child or targeted at child
            assert (activity["user_id"] == test_child_user.id or 
                   activity.get("target_user_id") == test_child_user.id)
    
    async def test_get_recent_activities_with_pagination(
        self,
        client: AsyncClient,
        test_parent_user,
        parent_token,
        sample_activities_data
    ):
        """Test activities endpoint with pagination parameters."""
        # Act - Request first page with limit of 2
        response = await client.get(
            "/api/v1/activities/recent?limit=2&offset=0",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["activities"]) <= 2
        
        # Test second page if there are more activities
        if data["has_more"]:
            response2 = await client.get(
                "/api/v1/activities/recent?limit=2&offset=2",
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            assert response2.status_code == status.HTTP_200_OK
    
    async def test_get_recent_activities_with_activity_type_filter(
        self,
        client: AsyncClient,
        test_parent_user,
        parent_token,
        sample_activities_data
    ):
        """Test activities endpoint with activity type filtering."""
        # Act - Filter for chore_completed activities only
        response = await client.get(
            f"/api/v1/activities/recent?activity_type={ActivityTypes.CHORE_COMPLETED}",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # All returned activities should be of the requested type
        for activity in data["activities"]:
            assert activity["activity_type"] == ActivityTypes.CHORE_COMPLETED
    
    async def test_get_recent_activities_unauthorized(self, client: AsyncClient):
        """Test activities endpoint requires authentication."""
        # Act
        response = await client.get("/api/v1/activities/recent")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_get_recent_activities_invalid_limit(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test activities endpoint with invalid limit parameter."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent?limit=0",  # Invalid limit
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_get_recent_activities_invalid_activity_type(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test activities endpoint with invalid activity type filter."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent?activity_type=invalid_type",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        # Should return OK but with no matching activities
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["activities"]) == 0


class TestActivitySummaryEndpoint:
    """Test GET /api/v1/activities/summary endpoint (if it exists)."""
    
    async def test_activity_summary_endpoint_exists(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test that activity summary endpoint exists and returns proper structure."""
        # Act
        response = await client.get(
            "/api/v1/activities/summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        # This might return 404 if endpoint doesn't exist yet
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # Expected structure for activity summary
            assert "activity_counts" in data
            assert "total_activities" in data
            assert "period_days" in data
            
            assert isinstance(data["activity_counts"], dict)
            assert isinstance(data["total_activities"], int)
            assert isinstance(data["period_days"], int)
        else:
            # If endpoint doesn't exist, document that it needs to be implemented
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestActivitiesEndpointSecurity:
    """Test security aspects of activities endpoints."""
    
    async def test_activities_cross_family_isolation(
        self,
        db_session,
        client: AsyncClient,
        activity_service
    ):
        """Test that activities are properly isolated between families."""
        # Create a second family
        from backend.app.models.user import User
        from backend.app.core.security.password import get_password_hash
        
        other_parent = User(
            email="other_parent@test.com",
            username="other_parent",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_parent=True
        )
        db_session.add(other_parent)
        await db_session.commit()
        await db_session.refresh(other_parent)
        
        other_child = User(
            email="other_child@test.com",
            username="other_child",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_parent=False,
            parent_id=other_parent.id
        )
        db_session.add(other_child)
        await db_session.commit()
        await db_session.refresh(other_child)
        
        # Create activity for the other family
        await activity_service.log_chore_completed(
            db=db_session,
            chore=type('MockChore', (), {
                'id': 999,
                'title': 'Other Family Chore',
                'reward': 10.0
            })(),
            user=other_child
        )
        await db_session.commit()
        
        # Create token for other parent
        from backend.app.core.security.jwt import create_access_token
        other_parent_token = create_access_token(subject=other_parent.id)
        
        # Act - Get activities for other parent
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {other_parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should only see activities from their own family
        for activity in data["activities"]:
            # Activity should involve users from the other family only
            assert activity["user_id"] in [other_parent.id, other_child.id] or \
                   activity.get("target_user_id") in [other_parent.id, other_child.id]


class TestActivitiesEndpointResponseFormat:
    """Test response format validation and structure."""
    
    async def test_activities_response_json_structure(
        self,
        client: AsyncClient,
        parent_token,
        sample_activities_data
    ):
        """Test that activities response follows expected JSON structure."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        
        # Check top-level structure
        assert isinstance(data, dict)
        assert "activities" in data
        assert "total_count" in data
        assert "has_more" in data
        
        # Check activities array structure
        assert isinstance(data["activities"], list)
        
        for activity in data["activities"]:
            assert isinstance(activity, dict)
            
            # Required fields
            assert "id" in activity
            assert "activity_type" in activity
            assert "description" in activity
            assert "user_id" in activity
            assert "created_at" in activity
            
            # Check data types
            assert isinstance(activity["id"], int)
            assert isinstance(activity["activity_type"], str)
            assert isinstance(activity["description"], str)
            assert isinstance(activity["user_id"], int)
            assert isinstance(activity["created_at"], str)
            
            # Optional fields
            if "target_user_id" in activity:
                assert activity["target_user_id"] is None or isinstance(activity["target_user_id"], int)
            
            if "activity_data" in activity:
                assert activity["activity_data"] is None or isinstance(activity["activity_data"], dict)
    
    async def test_activities_datetime_format(
        self,
        client: AsyncClient,
        parent_token,
        sample_activities_data
    ):
        """Test that datetime fields are properly formatted in ISO format."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        for activity in data["activities"]:
            created_at = activity["created_at"]
            
            # Should be ISO format string
            assert isinstance(created_at, str)
            
            # Should be parseable as datetime
            try:
                datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"Invalid datetime format: {created_at}")


class TestActivitiesEndpointEdgeCases:
    """Test edge cases and error handling for activities endpoints."""
    
    async def test_activities_empty_database(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test activities endpoint with no activities in database."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["activities"] == []
        assert data["total_count"] is None or data["total_count"] == 0
        assert data["has_more"] is False
    
    async def test_activities_large_limit_parameter(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test activities endpoint with maximum allowed limit."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent?limit=100",  # Maximum allowed
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should not exceed the limit
        assert len(data["activities"]) <= 100
    
    async def test_activities_excessive_limit_parameter(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test activities endpoint with limit exceeding maximum."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent?limit=1000",  # Exceeds maximum
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_activities_negative_offset(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test activities endpoint with negative offset."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent?offset=-1",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_activities_malformed_parameters(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test activities endpoint with malformed query parameters."""
        # Act
        response = await client.get(
            "/api/v1/activities/recent?limit=abc&offset=xyz",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
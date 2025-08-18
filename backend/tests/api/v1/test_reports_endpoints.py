"""
Comprehensive integration tests for reports API endpoints.

This test suite validates financial accuracy, authentication, authorization,
export functionality, and response formats for all reports endpoints using
real database operations with test data.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from fastapi import status
from httpx import AsyncClient

from backend.app.services.activity_service import ActivityService
from backend.app.models.reward_adjustment import RewardAdjustment
from backend.app.models.chore import Chore


@pytest_asyncio.fixture
async def activity_service():
    """Create real activity service instance."""
    return ActivityService()


@pytest_asyncio.fixture
async def test_chores(db_session, test_parent_user, test_child_user):
    """Create test chores for financial calculations."""
    # Create completed chores for testing
    chore1 = Chore(
        title="Clean Room",
        description="Clean and organize bedroom",
        reward=5.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=5.0,
        completion_date=datetime.now() - timedelta(days=2),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    chore2 = Chore(
        title="Do Dishes",
        description="Wash and put away dishes",
        reward=3.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=3.0,
        completion_date=datetime.now() - timedelta(days=1),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    # Create pending chore
    chore3 = Chore(
        title="Take Out Trash",
        description="Empty all trash cans",
        reward=2.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=False,
        completion_date=datetime.now(),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    db_session.add_all([chore1, chore2, chore3])
    await db_session.commit()
    await db_session.refresh(chore1)
    await db_session.refresh(chore2)
    await db_session.refresh(chore3)
    
    return [chore1, chore2, chore3]


@pytest_asyncio.fixture
async def test_adjustments(db_session, test_parent_user, test_child_user):
    """Create test reward adjustments."""
    adjustment1 = RewardAdjustment(
        child_id=test_child_user.id,
        parent_id=test_parent_user.id,
        amount=Decimal("2.50"),
        reason="Bonus for excellent work"
    )
    
    adjustment2 = RewardAdjustment(
        child_id=test_child_user.id,
        parent_id=test_parent_user.id,
        amount=Decimal("-1.00"),
        reason="Penalty for not following instructions"
    )
    
    db_session.add_all([adjustment1, adjustment2])
    await db_session.commit()
    await db_session.refresh(adjustment1)
    await db_session.refresh(adjustment2)
    
    return [adjustment1, adjustment2]


@pytest_asyncio.fixture
async def financial_test_data(db_session, test_parent_user, test_child_user, test_chores, test_adjustments, activity_service):
    """Create comprehensive financial test data with activities."""
    # Log activities for the completed chores
    await activity_service.log_chore_completed(
        db=db_session,
        child_id=test_child_user.id,
        chore_id=test_chores[0].id,
        chore_title=test_chores[0].title
    )
    
    await activity_service.log_chore_approved(
        db=db_session,
        parent_id=test_parent_user.id,
        child_id=test_child_user.id,
        chore_id=test_chores[0].id,
        chore_title=test_chores[0].title,
        reward_amount=5.0
    )
    
    await activity_service.log_chore_completed(
        db=db_session,
        child_id=test_child_user.id,
        chore_id=test_chores[1].id,
        chore_title=test_chores[1].title
    )
    
    await activity_service.log_chore_approved(
        db=db_session,
        parent_id=test_parent_user.id,
        child_id=test_child_user.id,
        chore_id=test_chores[1].id,
        chore_title=test_chores[1].title,
        reward_amount=3.0
    )
    
    # Log adjustment activities
    await activity_service.log_adjustment_applied(
        db=db_session,
        parent_id=test_parent_user.id,
        child_id=test_child_user.id,
        adjustment_id=test_adjustments[0].id,
        amount=2.50,
        reason="Bonus for excellent work"
    )
    
    await activity_service.log_adjustment_applied(
        db=db_session,
        parent_id=test_parent_user.id,
        child_id=test_child_user.id,
        adjustment_id=test_adjustments[1].id,
        amount=-1.00,
        reason="Penalty for not following instructions"
    )
    
    await db_session.commit()
    
    return {
        'chores': test_chores,
        'adjustments': test_adjustments,
        'expected_total_earned': 8.0,  # 5.0 + 3.0
        'expected_total_adjustments': 1.50,  # 2.50 - 1.00
        'expected_balance': 9.50,  # 8.0 + 1.50
        'expected_pending_value': 2.0  # pending chore
    }


class TestAllowanceSummaryEndpoint:
    """Test GET /api/v1/reports/allowance-summary endpoint."""
    
    async def test_allowance_summary_parent_access(
        self,
        client: AsyncClient,
        test_parent_user,
        parent_token,
        financial_test_data
    ):
        """Test parent can access comprehensive allowance summary."""
        # Act
        response = await client.get(
            "/api/v1/reports/allowance-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check top-level structure
        assert "family_summary" in data
        assert "child_summaries" in data
        
        # Verify family summary structure
        family_summary = data["family_summary"]
        assert "total_children" in family_summary
        assert "total_earned" in family_summary
        assert "total_adjustments" in family_summary
        assert "total_balance_due" in family_summary
        assert "total_completed_chores" in family_summary
        assert "period_start" in family_summary
        assert "period_end" in family_summary
        
        # Verify child summaries structure
        assert isinstance(data["child_summaries"], list)
        assert len(data["child_summaries"]) >= 1
        
        child_summary = data["child_summaries"][0]
        assert "id" in child_summary
        assert "username" in child_summary
        assert "completed_chores" in child_summary
        assert "total_earned" in child_summary
        assert "total_adjustments" in child_summary
        assert "paid_out" in child_summary
        assert "balance_due" in child_summary
        assert "pending_chores_value" in child_summary
    
    async def test_allowance_summary_financial_accuracy(
        self,
        client: AsyncClient,
        test_parent_user,
        test_child_user,
        parent_token,
        financial_test_data
    ):
        """Test financial calculations are accurate."""
        # Act
        response = await client.get(
            "/api/v1/reports/allowance-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        family_summary = data["family_summary"]
        child_summary = data["child_summaries"][0]
        
        # Verify family totals match expected values
        assert family_summary["total_children"] == 1
        assert family_summary["total_completed_chores"] == 2
        
        # Verify child financial calculations
        assert child_summary["id"] == test_child_user.id
        assert child_summary["username"] == test_child_user.username
        assert child_summary["completed_chores"] == 2
        assert child_summary["total_earned"] == financial_test_data["expected_total_earned"]
        assert child_summary["total_adjustments"] == financial_test_data["expected_total_adjustments"]
        assert child_summary["balance_due"] == financial_test_data["expected_balance"]
        assert child_summary["pending_chores_value"] == financial_test_data["expected_pending_value"]
    
    async def test_allowance_summary_with_date_filter(
        self,
        client: AsyncClient,
        parent_token,
        financial_test_data
    ):
        """Test allowance summary with date range filtering."""
        # Act - Filter to last 7 days
        today = datetime.now().date()
        week_ago = (today - timedelta(days=7)).isoformat()
        today_str = today.isoformat()
        
        response = await client.get(
            f"/api/v1/reports/allowance-summary?date_from={week_ago}&date_to={today_str}",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should still include recent activities
        family_summary = data["family_summary"]
        assert family_summary["total_children"] >= 0
        assert isinstance(family_summary["total_earned"], (int, float))
        assert isinstance(family_summary["total_adjustments"], (int, float))
        
        # Verify date range is reflected in response
        period_start = datetime.fromisoformat(family_summary["period_start"].replace('Z', '+00:00'))
        period_end = datetime.fromisoformat(family_summary["period_end"].replace('Z', '+00:00'))
        assert period_start.date() >= datetime.fromisoformat(week_ago).date()
        assert period_end.date() <= datetime.fromisoformat(today_str).date()
    
    async def test_allowance_summary_child_access_forbidden(
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
    
    async def test_allowance_summary_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test allowance summary requires authentication."""
        # Act
        response = await client.get("/api/v1/reports/allowance-summary")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_allowance_summary_invalid_date_format(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test allowance summary with invalid date format."""
        # Act
        response = await client.get(
            "/api/v1/reports/allowance-summary?date_from=invalid-date&date_to=2025-08-18",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    async def test_allowance_summary_future_date_range(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test allowance summary with future date range."""
        # Act - Use future dates
        future_start = (datetime.now() + timedelta(days=30)).date().isoformat()
        future_end = (datetime.now() + timedelta(days=60)).date().isoformat()
        
        response = await client.get(
            f"/api/v1/reports/allowance-summary?date_from={future_start}&date_to={future_end}",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should return empty or zero values for future dates
        family_summary = data["family_summary"]
        assert family_summary["total_earned"] == 0.0
        assert family_summary["total_completed_chores"] == 0


class TestExportAllowanceSummaryEndpoint:
    """Test GET /api/v1/reports/export/allowance-summary endpoint."""
    
    async def test_export_allowance_summary_csv(
        self,
        client: AsyncClient,
        parent_token,
        financial_test_data
    ):
        """Test CSV export of allowance summary."""
        # Act
        response = await client.get(
            "/api/v1/reports/export/allowance-summary?format=csv",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "content" in data
        assert "content_type" in data
        assert "filename" in data
        
        assert data["content_type"] == "text/csv"
        assert data["filename"].endswith(".csv")
        assert "allowance_summary" in data["filename"]
        
        # Verify CSV content structure
        csv_content = data["content"]
        assert isinstance(csv_content, str)
        assert len(csv_content) > 0
        
        # Should contain headers and data
        lines = csv_content.strip().split('\n')
        assert len(lines) >= 2  # Header + at least one data row
        
        # Check for expected CSV headers
        header_line = lines[0].lower()
        assert "child" in header_line or "username" in header_line
        assert "earned" in header_line or "total" in header_line
    
    async def test_export_allowance_summary_json(
        self,
        client: AsyncClient,
        parent_token,
        financial_test_data
    ):
        """Test JSON export of allowance summary."""
        # Act
        response = await client.get(
            "/api/v1/reports/export/allowance-summary?format=json",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "content" in data
        assert "content_type" in data
        assert "filename" in data
        
        assert data["content_type"] == "application/json"
        assert data["filename"].endswith(".json")
        assert "allowance_summary" in data["filename"]
        
        # Verify JSON content is valid
        json_content = data["content"]
        assert isinstance(json_content, str)
        assert len(json_content) > 0
        
        # Should be parseable JSON
        import json
        try:
            parsed_json = json.loads(json_content)
            assert isinstance(parsed_json, dict)
            assert "family_summary" in parsed_json or "child_summaries" in parsed_json
        except json.JSONDecodeError:
            pytest.fail("Export content is not valid JSON")
    
    async def test_export_allowance_summary_default_format(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test export with default format (should be CSV)."""
        # Act
        response = await client.get(
            "/api/v1/reports/export/allowance-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Default should be CSV
        assert data["content_type"] == "text/csv"
        assert data["filename"].endswith(".csv")
    
    async def test_export_allowance_summary_invalid_format(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test export with invalid format."""
        # Act
        response = await client.get(
            "/api/v1/reports/export/allowance-summary?format=invalid",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    async def test_export_allowance_summary_child_access_forbidden(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child cannot export allowance summary."""
        # Act
        response = await client.get(
            "/api/v1/reports/export/allowance-summary?format=csv",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_export_allowance_summary_with_date_filter(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test export with date range filtering."""
        # Act
        today = datetime.now().date().isoformat()
        week_ago = (datetime.now().date() - timedelta(days=7)).isoformat()
        
        response = await client.get(
            f"/api/v1/reports/export/allowance-summary?format=csv&date_from={week_ago}&date_to={today}",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["content_type"] == "text/csv"
        assert len(data["content"]) > 0
        
        # Filename should reflect date range
        filename = data["filename"]
        assert "allowance_summary" in filename
        assert filename.endswith(".csv")


class TestRewardHistoryEndpoint:
    """Test GET /api/v1/reports/reward-history/{child_id} endpoint."""
    
    async def test_reward_history_parent_access(
        self,
        client: AsyncClient,
        test_child_user,
        parent_token,
        financial_test_data
    ):
        """Test parent can access child's reward history."""
        # Act
        response = await client.get(
            f"/api/v1/reports/reward-history/{test_child_user.id}",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
        
        # Should contain reward history entries
        if len(data) > 0:
            entry = data[0]
            assert "date" in entry or "created_at" in entry
            assert "type" in entry or "activity_type" in entry
            assert "amount" in entry or "reward" in entry or "description" in entry
    
    async def test_reward_history_child_own_access(
        self,
        client: AsyncClient,
        test_child_user,
        child_token,
        financial_test_data
    ):
        """Test child can access their own reward history."""
        # Act
        response = await client.get(
            f"/api/v1/reports/reward-history/{test_child_user.id}",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
    
    async def test_reward_history_child_other_access_forbidden(
        self,
        db_session,
        client: AsyncClient,
        test_parent_user,
        child_token,
        financial_test_data
    ):
        """Test child cannot access other child's reward history."""
        # Create another child
        from backend.app.models.user import User
        from backend.app.core.security.password import get_password_hash
        
        other_child = User(
            email="other_child@test.com",
            username="other_child",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_parent=False,
            parent_id=test_parent_user.id
        )
        db_session.add(other_child)
        await db_session.commit()
        await db_session.refresh(other_child)
        
        # Act
        response = await client.get(
            f"/api/v1/reports/reward-history/{other_child.id}",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_reward_history_nonexistent_child(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test reward history for nonexistent child."""
        # Act
        response = await client.get(
            "/api/v1/reports/reward-history/99999",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_reward_history_with_limit(
        self,
        client: AsyncClient,
        test_child_user,
        parent_token,
        financial_test_data
    ):
        """Test reward history with limit parameter."""
        # Act
        response = await client.get(
            f"/api/v1/reports/reward-history/{test_child_user.id}?limit=5",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 5
    
    async def test_reward_history_unauthorized(
        self,
        client: AsyncClient,
        test_child_user
    ):
        """Test reward history requires authentication."""
        # Act
        response = await client.get(f"/api/v1/reports/reward-history/{test_child_user.id}")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestReportsEndpointSecurity:
    """Test security aspects of reports endpoints."""
    
    async def test_reports_cross_family_isolation(
        self,
        db_session,
        client: AsyncClient,
        activity_service
    ):
        """Test that reports are properly isolated between families."""
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
        
        # Create financial data for the other family
        await activity_service.log_chore_completed(
            db=db_session,
            child_id=other_child.id,
            chore_id=999,
            chore_title="Other Family Chore"
        )
        await activity_service.log_chore_approved(
            db=db_session,
            parent_id=other_parent.id,
            child_id=other_child.id,
            chore_id=999,
            chore_title="Other Family Chore",
            reward_amount=10.0
        )
        await db_session.commit()
        
        # Create token for other parent
        from backend.app.core.security.jwt import create_access_token
        other_parent_token = create_access_token(subject=other_parent.id)
        
        # Act - Get allowance summary for other parent
        response = await client.get(
            "/api/v1/reports/allowance-summary",
            headers={"Authorization": f"Bearer {other_parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should only see data from their own family
        child_summaries = data["child_summaries"]
        for child_summary in child_summaries:
            assert child_summary["id"] == other_child.id
        
        # Family summary should reflect only their data
        family_summary = data["family_summary"]
        assert family_summary["total_children"] == 1


class TestReportsEndpointResponseFormat:
    """Test response format validation and structure."""
    
    async def test_allowance_summary_response_format(
        self,
        client: AsyncClient,
        parent_token,
        financial_test_data
    ):
        """Test allowance summary response follows expected format."""
        # Act
        response = await client.get(
            "/api/v1/reports/allowance-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        
        # Validate family summary structure
        family_summary = data["family_summary"]
        assert isinstance(family_summary["total_children"], int)
        assert isinstance(family_summary["total_earned"], (int, float))
        assert isinstance(family_summary["total_adjustments"], (int, float))
        assert isinstance(family_summary["total_balance_due"], (int, float))
        assert isinstance(family_summary["total_completed_chores"], int)
        # period_start can be None when no date filtering is applied
        assert family_summary["period_start"] is None or isinstance(family_summary["period_start"], str)
        assert isinstance(family_summary["period_end"], str)
        
        # Validate child summaries structure
        for child_summary in data["child_summaries"]:
            assert isinstance(child_summary["id"], int)
            assert isinstance(child_summary["username"], str)
            assert isinstance(child_summary["completed_chores"], int)
            assert isinstance(child_summary["total_earned"], (int, float))
            assert isinstance(child_summary["total_adjustments"], (int, float))
            assert isinstance(child_summary["paid_out"], (int, float))
            assert isinstance(child_summary["balance_due"], (int, float))
            assert isinstance(child_summary["pending_chores_value"], (int, float))
    
    async def test_export_response_format(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test export response follows expected format."""
        # Act
        response = await client.get(
            "/api/v1/reports/export/allowance-summary?format=csv",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate export response structure
        assert isinstance(data["content"], str)
        assert isinstance(data["content_type"], str)
        assert isinstance(data["filename"], str)
        
        # Validate content type
        assert data["content_type"] in ["text/csv", "application/json"]
        
        # Validate filename format
        filename = data["filename"]
        assert len(filename) > 0
        assert "." in filename
        file_extension = filename.split(".")[-1]
        assert file_extension in ["csv", "json"]


class TestReportsEndpointEdgeCases:
    """Test edge cases and error handling for reports endpoints."""
    
    async def test_allowance_summary_empty_family(
        self,
        db_session,
        client: AsyncClient
    ):
        """Test allowance summary for parent with no children."""
        # Create parent with no children
        from backend.app.models.user import User
        from backend.app.core.security.password import get_password_hash
        from backend.app.core.security.jwt import create_access_token
        
        lonely_parent = User(
            email="lonely_parent@test.com",
            username="lonely_parent",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_parent=True
        )
        db_session.add(lonely_parent)
        await db_session.commit()
        await db_session.refresh(lonely_parent)
        
        lonely_parent_token = create_access_token(subject=lonely_parent.id)
        
        # Act
        response = await client.get(
            "/api/v1/reports/allowance-summary",
            headers={"Authorization": f"Bearer {lonely_parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        family_summary = data["family_summary"]
        assert family_summary["total_children"] == 0
        assert family_summary["total_earned"] == 0.0
        assert family_summary["total_adjustments"] == 0.0
        assert family_summary["total_balance_due"] == 0.0
        assert family_summary["total_completed_chores"] == 0
        
        assert data["child_summaries"] == []
    
    async def test_export_empty_data(
        self,
        db_session,
        client: AsyncClient
    ):
        """Test export with no data."""
        # Create parent with no children
        from backend.app.models.user import User
        from backend.app.core.security.password import get_password_hash
        from backend.app.core.security.jwt import create_access_token
        
        empty_parent = User(
            email="empty_parent@test.com",
            username="empty_parent",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_parent=True
        )
        db_session.add(empty_parent)
        await db_session.commit()
        await db_session.refresh(empty_parent)
        
        empty_parent_token = create_access_token(subject=empty_parent.id)
        
        # Act
        response = await client.get(
            "/api/v1/reports/export/allowance-summary?format=csv",
            headers={"Authorization": f"Bearer {empty_parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["content_type"] == "text/csv"
        assert len(data["content"]) > 0  # Should have at least headers
        assert data["filename"].endswith(".csv")
    
    async def test_reward_history_invalid_child_id(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test reward history with invalid child ID format."""
        # Act
        response = await client.get(
            "/api/v1/reports/reward-history/invalid",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
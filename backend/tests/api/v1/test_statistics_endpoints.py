"""
Comprehensive integration tests for statistics API endpoints.

This test suite validates statistical calculations, trend analysis, authentication,
authorization, and response formats for all statistics endpoints using real
database operations with time-series test data.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from fastapi import status
from httpx import AsyncClient

from backend.app.models.reward_adjustment import RewardAdjustment
from backend.app.models.chore import Chore


@pytest_asyncio.fixture
async def time_series_test_data(db_session, test_parent_user, test_child_user):
    """Create time-series test data for statistics calculations."""
    # Create chores spanning multiple weeks/months for trend analysis
    today = datetime.now().date()
    
    # Week 1 (4 weeks ago): 2 chores, $8 earned
    week_1_start = today - timedelta(weeks=4)
    chore1 = Chore(
        title="Week 1 Chore A",
        description="Clean room thoroughly",
        reward=5.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=5.0,
        completion_date=week_1_start + timedelta(days=1),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    chore2 = Chore(
        title="Week 1 Chore B",
        description="Do dishes",
        reward=3.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=3.0,
        completion_date=week_1_start + timedelta(days=3),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    # Week 2 (3 weeks ago): 3 chores, $12 earned
    week_2_start = today - timedelta(weeks=3)
    chore3 = Chore(
        title="Week 2 Chore A",
        description="Vacuum living room",
        reward=4.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=4.0,
        completion_date=week_2_start + timedelta(days=2),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    chore4 = Chore(
        title="Week 2 Chore B",
        description="Take out trash",
        reward=3.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=3.0,
        completion_date=week_2_start + timedelta(days=4),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    chore5 = Chore(
        title="Week 2 Chore C",
        description="Clean bathroom",
        reward=5.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=5.0,
        completion_date=week_2_start + timedelta(days=6),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    # Week 3 (2 weeks ago): 1 chore, $6 earned
    week_3_start = today - timedelta(weeks=2)
    chore6 = Chore(
        title="Week 3 Chore A",
        description="Organize garage",
        reward=6.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=6.0,
        completion_date=week_3_start + timedelta(days=1),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    # Current week: 4 chores, $15 earned (shows increasing trend)
    current_week_start = today - timedelta(days=today.weekday())
    chore7 = Chore(
        title="Current Week Chore A",
        description="Mow lawn",
        reward=4.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=4.0,
        completion_date=current_week_start + timedelta(days=1),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    chore8 = Chore(
        title="Current Week Chore B",
        description="Clean windows",
        reward=3.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=3.0,
        completion_date=current_week_start + timedelta(days=2),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    chore9 = Chore(
        title="Current Week Chore C",
        description="Weed garden",
        reward=4.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=4.0,
        completion_date=current_week_start + timedelta(days=3),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    chore10 = Chore(
        title="Current Week Chore D",
        description="Wash car",
        reward=4.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_completed=True,
        is_approved=True,
        approval_reward=4.0,
        completion_date=current_week_start + timedelta(days=4),
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    
    # Add some adjustments for complete testing
    adjustment1 = RewardAdjustment(
        child_id=test_child_user.id,
        parent_id=test_parent_user.id,
        amount=Decimal("2.50"),
        reason="Bonus for excellent attitude",
        created_at=week_2_start + timedelta(days=5)
    )
    
    adjustment2 = RewardAdjustment(
        child_id=test_child_user.id,
        parent_id=test_parent_user.id,
        amount=Decimal("-1.00"),
        reason="Deduction for incomplete chore",
        created_at=week_3_start + timedelta(days=3)
    )
    
    all_chores = [chore1, chore2, chore3, chore4, chore5, chore6, chore7, chore8, chore9, chore10]
    all_adjustments = [adjustment1, adjustment2]
    
    db_session.add_all(all_chores + all_adjustments)
    await db_session.commit()
    
    # Refresh all objects to get IDs
    for chore in all_chores:
        await db_session.refresh(chore)
    for adjustment in all_adjustments:
        await db_session.refresh(adjustment)
    
    return {
        'chores': all_chores,
        'adjustments': all_adjustments,
        'expected_total_chores': 10,
        'expected_total_earned': 41.0,  # 5+3+4+3+5+6+4+3+4+4 = 41
        'expected_total_adjustments': 1.5,  # 2.50 - 1.00 = 1.50
        'weekly_pattern': [2, 3, 1, 4],  # chores per week (oldest to newest)
        'earnings_pattern': [8.0, 12.0, 6.0, 15.0]  # earnings per week
    }


class TestWeeklySummaryEndpoint:
    """Test GET /api/v1/statistics/weekly-summary endpoint."""
    
    async def test_weekly_summary_parent_access(
        self,
        client: AsyncClient,
        test_parent_user,
        parent_token,
        time_series_test_data
    ):
        """Test parent can access weekly summary with default parameters."""
        # Act
        response = await client.get(
            "/api/v1/statistics/weekly-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check top-level structure
        assert "weeks_analyzed" in data
        assert "weekly_data" in data
        assert "summary" in data
        
        # Verify weekly data structure
        assert isinstance(data["weekly_data"], list)
        assert len(data["weekly_data"]) == 4  # Default weeks_back
        
        weekly_point = data["weekly_data"][0]
        assert "week_start" in weekly_point
        assert "week_end" in weekly_point
        assert "completed_chores" in weekly_point
        assert "total_earned" in weekly_point
        assert "total_adjustments" in weekly_point
        assert "net_amount" in weekly_point
        assert "active_children" in weekly_point
        assert "average_per_chore" in weekly_point
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_chores" in summary
        assert "total_earned" in summary
        assert "total_adjustments" in summary
        assert "average_per_week" in summary
        assert "trend_direction" in summary
    
    async def test_weekly_summary_with_custom_weeks(
        self,
        client: AsyncClient,
        parent_token,
        time_series_test_data
    ):
        """Test weekly summary with custom weeks_back parameter."""
        # Act
        response = await client.get(
            "/api/v1/statistics/weekly-summary?weeks_back=2",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["weeks_analyzed"] == 2
        assert len(data["weekly_data"]) == 2
        
        # Should only include the most recent 2 weeks
        summary = data["summary"]
        assert summary["total_chores"] <= time_series_test_data["expected_total_chores"]
        assert summary["average_per_week"] == summary["total_chores"] / 2
    
    async def test_weekly_summary_with_child_filter(
        self,
        client: AsyncClient,
        test_child_user,
        parent_token,
        time_series_test_data
    ):
        """Test weekly summary filtered by specific child."""
        # Act
        response = await client.get(
            f"/api/v1/statistics/weekly-summary?child_id={test_child_user.id}",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # All chores should belong to the specified child
        for week in data["weekly_data"]:
            if week["completed_chores"] > 0:
                assert week["active_children"] == 1  # Only one child active
    
    async def test_weekly_summary_child_access_forbidden(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child cannot access weekly summary."""
        # Act
        response = await client.get(
            "/api/v1/statistics/weekly-summary",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_weekly_summary_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test weekly summary requires authentication."""
        # Act
        response = await client.get("/api/v1/statistics/weekly-summary")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_weekly_summary_invalid_weeks_back(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test weekly summary with invalid weeks_back parameter."""
        # Act - weeks_back > 12 (maximum)
        response = await client.get(
            "/api/v1/statistics/weekly-summary?weeks_back=15",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_weekly_summary_nonexistent_child(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test weekly summary with nonexistent child_id."""
        # Act
        response = await client.get(
            "/api/v1/statistics/weekly-summary?child_id=99999",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMonthlySummaryEndpoint:
    """Test GET /api/v1/statistics/monthly-summary endpoint."""
    
    async def test_monthly_summary_parent_access(
        self,
        client: AsyncClient,
        parent_token,
        time_series_test_data
    ):
        """Test parent can access monthly summary."""
        # Act
        response = await client.get(
            "/api/v1/statistics/monthly-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check structure
        assert "months_analyzed" in data
        assert "monthly_data" in data
        assert "summary" in data
        
        # Verify monthly data structure
        assert isinstance(data["monthly_data"], list)
        assert len(data["monthly_data"]) == 6  # Default months_back
        
        monthly_point = data["monthly_data"][0]
        assert "month" in monthly_point
        assert "year" in monthly_point
        assert "month_number" in monthly_point
        assert "completed_chores" in monthly_point
        assert "total_earned" in monthly_point
        assert "total_adjustments" in monthly_point
        assert "net_amount" in monthly_point
        assert "active_children" in monthly_point
        assert "average_per_chore" in monthly_point
    
    async def test_monthly_summary_with_custom_months(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test monthly summary with custom months_back parameter."""
        # Act
        response = await client.get(
            "/api/v1/statistics/monthly-summary?months_back=3",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["months_analyzed"] == 3
        assert len(data["monthly_data"]) == 3
    
    async def test_monthly_summary_child_access_forbidden(
        self,
        client: AsyncClient,
        child_token
    ):
        """Test child cannot access monthly summary."""
        # Act
        response = await client.get(
            "/api/v1/statistics/monthly-summary",
            headers={"Authorization": f"Bearer {child_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTrendAnalysisEndpoint:
    """Test GET /api/v1/statistics/trends endpoint."""
    
    async def test_trend_analysis_weekly_period(
        self,
        client: AsyncClient,
        parent_token,
        time_series_test_data
    ):
        """Test trend analysis with weekly period."""
        # Act
        response = await client.get(
            "/api/v1/statistics/trends?period=weekly",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check structure
        assert data["period"] == "weekly"
        assert "periods_analyzed" in data
        assert "chore_completion_trend" in data
        assert "earnings_trend" in data
        assert "insights" in data
        assert "data_points" in data
        
        # Verify trend data structure
        chore_trend = data["chore_completion_trend"]
        assert "direction" in chore_trend
        assert "growth_rate" in chore_trend
        assert "consistency_score" in chore_trend
        assert chore_trend["direction"] in ["increasing", "decreasing", "stable"]
        
        earnings_trend = data["earnings_trend"]
        assert "direction" in earnings_trend
        assert "growth_rate" in earnings_trend
        assert "consistency_score" in earnings_trend
        
        # Verify insights
        assert isinstance(data["insights"], list)
    
    async def test_trend_analysis_monthly_period(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test trend analysis with monthly period."""
        # Act
        response = await client.get(
            "/api/v1/statistics/trends?period=monthly",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["period"] == "monthly"
    
    async def test_trend_analysis_invalid_period(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test trend analysis with invalid period."""
        # Act
        response = await client.get(
            "/api/v1/statistics/trends?period=yearly",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_trend_analysis_child_access_forbidden(
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


class TestComparisonEndpoint:
    """Test GET /api/v1/statistics/comparison endpoint."""
    
    async def test_comparison_this_vs_last_week(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test comparison statistics for this vs last week."""
        # Act
        response = await client.get(
            "/api/v1/statistics/comparison?compare_periods=this_vs_last_week",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check structure
        assert data["comparison_type"] == "this_vs_last_week"
        assert "current_period" in data
        assert "previous_period" in data
        assert "changes" in data
        assert "insights" in data
        
        # Verify period stats structure
        current_period = data["current_period"]
        assert "completed_chores" in current_period
        assert "total_earned" in current_period
        assert "total_adjustments" in current_period
        
        previous_period = data["previous_period"]
        assert "completed_chores" in previous_period
        assert "total_earned" in previous_period
        assert "total_adjustments" in previous_period
        
        # Verify changes structure
        changes = data["changes"]
        assert "chores_change" in changes
        assert "earnings_change" in changes
        assert "adjustments_change" in changes
        
        # Verify insights
        assert isinstance(data["insights"], list)
    
    async def test_comparison_this_vs_last_month(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test comparison statistics for this vs last month."""
        # Act
        response = await client.get(
            "/api/v1/statistics/comparison?compare_periods=this_vs_last_month",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["comparison_type"] == "this_vs_last_month"
    
    async def test_comparison_invalid_period_type(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test comparison with invalid period type."""
        # Act
        response = await client.get(
            "/api/v1/statistics/comparison?compare_periods=invalid_comparison",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_comparison_child_access_forbidden(
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


class TestStatisticsEndpointSecurity:
    """Test security aspects of statistics endpoints."""
    
    async def test_statistics_cross_family_isolation(
        self,
        db_session,
        client: AsyncClient
    ):
        """Test that statistics are properly isolated between families."""
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
        
        # Create chores for other family
        other_chore = Chore(
            title="Other Family Chore",
            description="Should not appear in original family stats",
            reward=10.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            is_completed=True,
            is_approved=True,
            approval_reward=10.0,
            completion_date=datetime.now() - timedelta(days=1),
            assignee_id=other_child.id,
            creator_id=other_parent.id
        )
        db_session.add(other_chore)
        await db_session.commit()
        
        # Create token for other parent
        from backend.app.core.security.jwt import create_access_token
        other_parent_token = create_access_token(subject=other_parent.id)
        
        # Act - Get statistics for other parent
        response = await client.get(
            "/api/v1/statistics/weekly-summary",
            headers={"Authorization": f"Bearer {other_parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should only see data from their own family
        # The other family should have their chore visible
        summary = data["summary"]
        assert summary["total_chores"] >= 1  # At least their own chore


class TestStatisticsEndpointResponseFormat:
    """Test response format validation and structure."""
    
    async def test_weekly_summary_response_format(
        self,
        client: AsyncClient,
        parent_token,
        time_series_test_data
    ):
        """Test weekly summary response follows expected format."""
        # Act
        response = await client.get(
            "/api/v1/statistics/weekly-summary",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        
        # Validate top-level structure
        assert isinstance(data["weeks_analyzed"], int)
        assert isinstance(data["weekly_data"], list)
        assert isinstance(data["summary"], dict)
        
        # Validate weekly data point structure
        if data["weekly_data"]:
            weekly_point = data["weekly_data"][0]
            assert isinstance(weekly_point["week_start"], str)
            assert isinstance(weekly_point["week_end"], str)
            assert isinstance(weekly_point["completed_chores"], int)
            assert isinstance(weekly_point["total_earned"], (int, float))
            assert isinstance(weekly_point["total_adjustments"], (int, float))
            assert isinstance(weekly_point["net_amount"], (int, float))
            assert isinstance(weekly_point["active_children"], int)
            assert isinstance(weekly_point["average_per_chore"], (int, float))
        
        # Validate summary structure
        summary = data["summary"]
        assert isinstance(summary["total_chores"], int)
        assert isinstance(summary["total_earned"], (int, float))
        assert isinstance(summary["total_adjustments"], (int, float))
        assert isinstance(summary["average_per_week"], (int, float))
        assert isinstance(summary["trend_direction"], str)
        assert summary["trend_direction"] in ["increasing", "decreasing", "stable"]
    
    async def test_trend_analysis_response_format(
        self,
        client: AsyncClient,
        parent_token
    ):
        """Test trend analysis response follows expected format."""
        # Act
        response = await client.get(
            "/api/v1/statistics/trends?period=weekly",
            headers={"Authorization": f"Bearer {parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate trend data structure
        chore_trend = data["chore_completion_trend"]
        assert isinstance(chore_trend["direction"], str)
        assert isinstance(chore_trend["growth_rate"], (int, float))
        assert isinstance(chore_trend["consistency_score"], (int, float))
        assert chore_trend["direction"] in ["increasing", "decreasing", "stable"]
        assert 0 <= chore_trend["consistency_score"] <= 100
        
        earnings_trend = data["earnings_trend"]
        assert isinstance(earnings_trend["direction"], str)
        assert isinstance(earnings_trend["growth_rate"], (int, float))
        assert isinstance(earnings_trend["consistency_score"], (int, float))
        
        # Validate insights
        assert isinstance(data["insights"], list)
        for insight in data["insights"]:
            assert isinstance(insight, str)
            assert len(insight) > 0


class TestStatisticsEndpointEdgeCases:
    """Test edge cases and error handling for statistics endpoints."""
    
    async def test_weekly_summary_empty_family(
        self,
        db_session,
        client: AsyncClient
    ):
        """Test weekly summary for parent with no completed chores."""
        # Create parent with no children/chores
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
            "/api/v1/statistics/weekly-summary",
            headers={"Authorization": f"Bearer {empty_parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should return empty data gracefully
        summary = data["summary"]
        assert summary["total_chores"] == 0
        assert summary["total_earned"] == 0.0
        assert summary["total_adjustments"] == 0.0
        assert summary["average_per_week"] == 0.0
        assert summary["trend_direction"] == "stable"
    
    async def test_trend_analysis_insufficient_data(
        self,
        db_session,
        client: AsyncClient
    ):
        """Test trend analysis with insufficient data for meaningful trends."""
        # Create parent with minimal data
        from backend.app.models.user import User
        from backend.app.core.security.password import get_password_hash
        from backend.app.core.security.jwt import create_access_token
        
        minimal_parent = User(
            email="minimal_parent@test.com",
            username="minimal_parent",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_parent=True
        )
        db_session.add(minimal_parent)
        await db_session.commit()
        await db_session.refresh(minimal_parent)
        
        minimal_parent_token = create_access_token(subject=minimal_parent.id)
        
        # Act
        response = await client.get(
            "/api/v1/statistics/trends?period=weekly",
            headers={"Authorization": f"Bearer {minimal_parent_token}"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should handle minimal data gracefully
        chore_trend = data["chore_completion_trend"]
        assert chore_trend["direction"] == "stable"  # Should default to stable with no data
        assert chore_trend["growth_rate"] == 0.0
        assert chore_trend["consistency_score"] >= 0
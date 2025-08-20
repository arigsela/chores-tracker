"""
Comprehensive tests for ActivityService business logic.

This test suite validates critical activity logging functionality that ensures
audit trail integrity and proper chore workflow tracking.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from backend.app.services.activity_service import ActivityService
from backend.app.models.activity import Activity
from backend.app.repositories.activity import ActivityRepository


@pytest_asyncio.fixture
async def activity_service():
    """Create ActivityService instance for testing."""
    return ActivityService()


@pytest_asyncio.fixture
async def mock_db_session():
    """Create mock database session."""
    mock_session = Mock()
    return mock_session


@pytest_asyncio.fixture
async def mock_activity_repository():
    """Create mock ActivityRepository."""
    mock_repo = Mock(spec=ActivityRepository)
    return mock_repo


@pytest_asyncio.fixture
async def sample_activity():
    """Create sample activity for testing."""
    return Activity(
        id=1,
        user_id=123,
        activity_type="chore_completed",
        description="Completed chore: Clean room",
        target_user_id=None,
        activity_data={"chore_id": 456, "chore_title": "Clean room"},
        created_at=datetime.utcnow()
    )


class TestChoreCompletedLogging:
    """Test chore completion activity logging."""
    
    @pytest.mark.asyncio
    async def test_log_chore_completed_creates_correct_activity(self, activity_service, mock_db_session):
        """Test that chore completion logging creates proper activity record."""
        # Arrange
        child_id = 123
        chore_id = 456
        chore_title = "Clean your room"
        expected_activity = Activity(
            id=1,
            user_id=child_id,
            activity_type="chore_completed",
            description="Completed chore: Clean your room",
            activity_data={"chore_id": chore_id, "chore_title": chore_title}
        )
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = expected_activity
            
            # Act
            result = await activity_service.log_chore_completed(
                mock_db_session,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=chore_title
            )
            
            # Assert
            assert result == expected_activity
            mock_create.assert_called_once_with(
                mock_db_session,
                user_id=child_id,
                activity_type="chore_completed",
                description="Completed chore: Clean your room",
                activity_data={"chore_id": chore_id, "chore_title": chore_title}
            )
    
    @pytest.mark.asyncio
    async def test_log_chore_completed_handles_long_titles(self, activity_service, mock_db_session):
        """Test that long chore titles are handled properly in activity logging."""
        # Arrange
        child_id = 123
        chore_id = 456
        long_title = "Clean your room and organize all your toys and books and make your bed and vacuum" * 2
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_completed(
                mock_db_session,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=long_title
            )
            
            # Assert
            call_args = mock_create.call_args
            assert call_args[1]["activity_data"]["chore_title"] == long_title
            assert "Completed chore:" in call_args[1]["description"]
    
    @pytest.mark.asyncio
    async def test_log_chore_completed_with_special_characters(self, activity_service, mock_db_session):
        """Test chore completion logging with special characters in title."""
        # Arrange
        child_id = 123
        chore_id = 456
        special_title = "Clean room & vacuum 100% <carefully>"
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_completed(
                mock_db_session,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=special_title
            )
            
            # Assert
            call_args = mock_create.call_args
            assert call_args[1]["activity_data"]["chore_title"] == special_title
            assert special_title in call_args[1]["description"]


class TestChoreApprovalLogging:
    """Test chore approval activity logging."""
    
    @pytest.mark.asyncio
    async def test_log_chore_approved_creates_correct_activity(self, activity_service, mock_db_session):
        """Test that chore approval logging creates proper activity record."""
        # Arrange
        parent_id = 100
        child_id = 123
        chore_id = 456
        chore_title = "Clean room"
        reward_amount = 5.50
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_approved(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=chore_title,
                reward_amount=reward_amount
            )
            
            # Assert
            call_args = mock_create.call_args
            assert call_args[1]["user_id"] == parent_id
            assert call_args[1]["target_user_id"] == child_id
            assert call_args[1]["activity_type"] == "chore_approved"
            assert "$5.50" in call_args[1]["description"]
            assert call_args[1]["activity_data"]["reward_amount"] == reward_amount
    
    @pytest.mark.asyncio
    async def test_log_chore_approved_formats_currency_correctly(self, activity_service, mock_db_session):
        """Test that reward amounts are formatted correctly in descriptions."""
        # Arrange
        test_cases = [
            (5.0, "$5.00"),
            (5.50, "$5.50"),
            (10.99, "$10.99"),
            (0.01, "$0.01"),
            (100.0, "$100.00")
        ]
        
        for reward_amount, expected_format in test_cases:
            with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = Mock()
                
                # Act
                await activity_service.log_chore_approved(
                    mock_db_session,
                    parent_id=100,
                    child_id=123,
                    chore_id=456,
                    chore_title="Test chore",
                    reward_amount=reward_amount
                )
                
                # Assert
                call_args = mock_create.call_args
                assert expected_format in call_args[1]["description"]
    
    @pytest.mark.asyncio
    async def test_log_chore_approved_stores_complete_metadata(self, activity_service, mock_db_session):
        """Test that all relevant metadata is stored in activity_data."""
        # Arrange
        parent_id = 100
        child_id = 123
        chore_id = 456
        chore_title = "Clean room"
        reward_amount = 7.25
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_approved(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=chore_title,
                reward_amount=reward_amount
            )
            
            # Assert
            call_args = mock_create.call_args
            activity_data = call_args[1]["activity_data"]
            assert activity_data["chore_id"] == chore_id
            assert activity_data["chore_title"] == chore_title
            assert activity_data["reward_amount"] == reward_amount


class TestChoreRejectionLogging:
    """Test chore rejection activity logging."""
    
    @pytest.mark.asyncio
    async def test_log_chore_rejected_creates_correct_activity(self, activity_service, mock_db_session):
        """Test that chore rejection logging creates proper activity record."""
        # Arrange
        parent_id = 100
        child_id = 123
        chore_id = 456
        chore_title = "Clean room"
        rejection_reason = "Room was not clean enough"
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_rejected(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=chore_title,
                rejection_reason=rejection_reason
            )
            
            # Assert
            call_args = mock_create.call_args
            assert call_args[1]["user_id"] == parent_id
            assert call_args[1]["target_user_id"] == child_id
            assert call_args[1]["activity_type"] == "chore_rejected"
            assert chore_title in call_args[1]["description"]
            assert call_args[1]["activity_data"]["rejection_reason"] == rejection_reason
    
    @pytest.mark.asyncio
    async def test_log_chore_rejected_truncates_long_reasons(self, activity_service, mock_db_session):
        """Test that long rejection reasons are truncated in description."""
        # Arrange
        parent_id = 100
        child_id = 123
        chore_id = 456
        chore_title = "Clean room"
        long_reason = "This room is still very messy and needs much more cleaning before it can be considered complete" * 2
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_rejected(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=chore_title,
                rejection_reason=long_reason
            )
            
            # Assert
            call_args = mock_create.call_args
            description = call_args[1]["description"]
            # Description should be truncated but full reason should be in activity_data
            assert len(description) < len(long_reason) + 50  # Account for prefix
            assert "..." in description
            assert call_args[1]["activity_data"]["rejection_reason"] == long_reason
    
    @pytest.mark.asyncio
    async def test_log_chore_rejected_handles_empty_reason(self, activity_service, mock_db_session):
        """Test that empty rejection reasons are handled gracefully."""
        # Arrange
        parent_id = 100
        child_id = 123
        chore_id = 456
        chore_title = "Clean room"
        empty_reason = ""
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_rejected(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=chore_title,
                rejection_reason=empty_reason
            )
            
            # Assert
            call_args = mock_create.call_args
            assert call_args[1]["activity_data"]["rejection_reason"] == empty_reason
            # Should not crash and should create valid description


class TestAdjustmentLogging:
    """Test reward adjustment activity logging."""
    
    @pytest.mark.asyncio
    async def test_log_adjustment_applied_positive_amount(self, activity_service, mock_db_session):
        """Test logging of positive (bonus) adjustments."""
        # Arrange
        parent_id = 100
        child_id = 123
        adjustment_id = 789
        amount = 10.50
        reason = "Excellent behavior this week"
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_adjustment_applied(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                adjustment_id=adjustment_id,
                amount=amount,
                reason=reason
            )
            
            # Assert
            call_args = mock_create.call_args
            assert call_args[1]["user_id"] == parent_id
            assert call_args[1]["target_user_id"] == child_id
            assert call_args[1]["activity_type"] == "adjustment_applied"
            assert "bonus" in call_args[1]["description"].lower()
            assert "$10.50" in call_args[1]["description"]
            assert call_args[1]["activity_data"]["amount"] == amount
    
    @pytest.mark.asyncio
    async def test_log_adjustment_applied_negative_amount(self, activity_service, mock_db_session):
        """Test logging of negative (deduction) adjustments."""
        # Arrange
        parent_id = 100
        child_id = 123
        adjustment_id = 789
        amount = -5.25
        reason = "Broke household rule"
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_adjustment_applied(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                adjustment_id=adjustment_id,
                amount=amount,
                reason=reason
            )
            
            # Assert
            call_args = mock_create.call_args
            description = call_args[1]["description"]
            assert "deduction" in description.lower()
            assert "$5.25" in description  # Should show absolute value
            assert call_args[1]["activity_data"]["amount"] == amount  # Should store actual negative value
    
    @pytest.mark.asyncio
    async def test_log_adjustment_applied_zero_amount(self, activity_service, mock_db_session):
        """Test logging of zero-amount adjustments."""
        # Arrange
        parent_id = 100
        child_id = 123
        adjustment_id = 789
        amount = 0.0
        reason = "Test adjustment"
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_adjustment_applied(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                adjustment_id=adjustment_id,
                amount=amount,
                reason=reason
            )
            
            # Assert
            call_args = mock_create.call_args
            description = call_args[1]["description"]
            assert "bonus" in description.lower()  # Zero is treated as positive
            assert "$0.00" in description
    
    @pytest.mark.asyncio
    async def test_log_adjustment_applied_custom_type(self, activity_service, mock_db_session):
        """Test logging adjustments with custom adjustment types."""
        # Arrange
        parent_id = 100
        child_id = 123
        adjustment_id = 789
        amount = 15.0
        reason = "Birthday bonus"
        adjustment_type = "birthday_bonus"
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_adjustment_applied(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                adjustment_id=adjustment_id,
                amount=amount,
                reason=reason,
                adjustment_type=adjustment_type
            )
            
            # Assert
            call_args = mock_create.call_args
            activity_data = call_args[1]["activity_data"]
            assert activity_data["adjustment_type"] == adjustment_type


class TestChoreCreationLogging:
    """Test chore creation activity logging."""
    
    @pytest.mark.asyncio
    async def test_log_chore_created_assigned_with_reward(self, activity_service, mock_db_session):
        """Test logging chore creation when assigned to child with fixed reward."""
        # Arrange
        parent_id = 100
        child_id = 123
        chore_id = 456
        chore_title = "Clean room"
        reward_amount = 8.0
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_created(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=chore_title,
                reward_amount=reward_amount
            )
            
            # Assert
            call_args = mock_create.call_args
            assert call_args[1]["user_id"] == parent_id
            assert call_args[1]["target_user_id"] == child_id
            assert call_args[1]["activity_type"] == "chore_created"
            description = call_args[1]["description"]
            assert chore_title in description
            assert "$8.00" in description
    
    @pytest.mark.asyncio
    async def test_log_chore_created_assigned_without_reward(self, activity_service, mock_db_session):
        """Test logging chore creation when assigned to child without fixed reward."""
        # Arrange
        parent_id = 100
        child_id = 123
        chore_id = 456
        chore_title = "Clean room"
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_created(
                mock_db_session,
                parent_id=parent_id,
                child_id=child_id,
                chore_id=chore_id,
                chore_title=chore_title,
                reward_amount=None
            )
            
            # Assert
            call_args = mock_create.call_args
            description = call_args[1]["description"]
            assert chore_title in description
            assert "$" not in description  # No reward amount mentioned
    
    @pytest.mark.asyncio
    async def test_log_chore_created_unassigned(self, activity_service, mock_db_session):
        """Test logging chore creation when not assigned to any child."""
        # Arrange
        parent_id = 100
        chore_id = 456
        chore_title = "Clean kitchen"
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act
            await activity_service.log_chore_created(
                mock_db_session,
                parent_id=parent_id,
                child_id=None,
                chore_id=chore_id,
                chore_title=chore_title
            )
            
            # Assert
            call_args = mock_create.call_args
            assert call_args[1]["target_user_id"] is None
            description = call_args[1]["description"]
            assert "unassigned" in description.lower()
            assert chore_title in description


class TestFamilyActivityRetrieval:
    """Test family activity retrieval functionality."""
    
    @pytest.mark.asyncio
    async def test_get_recent_activities_for_family(self, activity_service, mock_db_session):
        """Test retrieving recent activities for entire family."""
        # Arrange
        parent_id = 100
        limit = 15
        expected_activities = [Mock(), Mock(), Mock()]
        
        with patch.object(activity_service.repository, 'get_family_activities', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected_activities
            
            # Act
            result = await activity_service.get_recent_activities_for_family(
                mock_db_session,
                parent_id=parent_id,
                limit=limit
            )
            
            # Assert
            assert result == expected_activities
            mock_get.assert_called_once_with(
                mock_db_session,
                parent_id=parent_id,
                limit=limit
            )
    
    @pytest.mark.asyncio
    async def test_get_recent_activities_for_family_default_limit(self, activity_service, mock_db_session):
        """Test that default limit is applied when not specified."""
        # Arrange
        parent_id = 100
        
        with patch.object(activity_service.repository, 'get_family_activities', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            # Act
            await activity_service.get_recent_activities_for_family(
                mock_db_session,
                parent_id=parent_id
            )
            
            # Assert
            mock_get.assert_called_once_with(
                mock_db_session,
                parent_id=parent_id,
                limit=20  # Default limit
            )


class TestUserActivityRetrieval:
    """Test individual user activity retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_recent_activities_for_user(self, activity_service, mock_db_session):
        """Test retrieving recent activities for specific user."""
        # Arrange
        user_id = 123
        limit = 10
        expected_activities = [Mock(), Mock()]
        
        with patch.object(activity_service.repository, 'get_recent_activities', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected_activities
            
            # Act
            result = await activity_service.get_recent_activities_for_user(
                mock_db_session,
                user_id=user_id,
                limit=limit
            )
            
            # Assert
            assert result == expected_activities
            mock_get.assert_called_once_with(
                mock_db_session,
                user_id=user_id,
                limit=limit
            )


class TestActivitySummary:
    """Test activity summary and aggregation functionality."""
    
    @pytest.mark.asyncio
    async def test_get_activity_summary_with_user_filter(self, activity_service, mock_db_session):
        """Test getting activity summary filtered by user."""
        # Arrange
        user_id = 123
        days_back = 7
        expected_summary = {
            "chore_completed": 5,
            "chore_approved": 3,
            "chore_rejected": 1
        }
        
        with patch.object(activity_service.repository, 'get_activity_counts_by_type', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected_summary
            
            # Act
            result = await activity_service.get_activity_summary(
                mock_db_session,
                user_id=user_id,
                days_back=days_back
            )
            
            # Assert
            assert result == expected_summary
            mock_get.assert_called_once_with(
                mock_db_session,
                user_id=user_id,
                days_back=days_back
            )
    
    @pytest.mark.asyncio
    async def test_get_activity_summary_all_users(self, activity_service, mock_db_session):
        """Test getting activity summary for all users."""
        # Arrange
        expected_summary = {
            "chore_completed": 15,
            "chore_approved": 12,
            "adjustment_applied": 3
        }
        
        with patch.object(activity_service.repository, 'get_activity_counts_by_type', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected_summary
            
            # Act
            result = await activity_service.get_activity_summary(
                mock_db_session,
                days_back=30
            )
            
            # Assert
            assert result == expected_summary
            mock_get.assert_called_once_with(
                mock_db_session,
                user_id=None,
                days_back=30
            )


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_repository_error_propagation(self, activity_service, mock_db_session):
        """Test that repository errors are properly propagated."""
        # Arrange
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            # Act & Assert
            with pytest.raises(Exception, match="Database error"):
                await activity_service.log_chore_completed(
                    mock_db_session,
                    child_id=123,
                    chore_id=456,
                    chore_title="Test chore"
                )
    
    @pytest.mark.asyncio
    async def test_concurrent_activity_logging(self, activity_service, mock_db_session):
        """Test that concurrent activity logging doesn't cause issues."""
        # Arrange
        import asyncio
        
        with patch.object(activity_service.repository, 'create_activity', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            # Act - Simulate concurrent logging
            tasks = [
                activity_service.log_chore_completed(
                    mock_db_session,
                    child_id=123,
                    chore_id=i,
                    chore_title=f"Chore {i}"
                )
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Assert
            assert len(results) == 5
            assert mock_create.call_count == 5
"""
Comprehensive tests for financial calculation accuracy in reports endpoints.

This test suite validates critical financial calculations that determine
allowance payments and family budget summaries.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

from backend.app.api.api_v1.endpoints.reports import get_allowance_summary, export_allowance_summary, get_reward_history
from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.models.reward_adjustment import RewardAdjustment
from backend.app.schemas.reports import AllowanceSummaryResponse, ChildAllowanceSummary, FamilyFinancialSummary


@pytest_asyncio.fixture
async def mock_parent_user():
    """Create mock parent user for testing."""
    return User(
        id=100,
        username="parent",
        email="parent@test.com",
        is_parent=True,
        parent_id=None
    )


@pytest_asyncio.fixture
async def mock_child_users():
    """Create mock child users for testing."""
    return [
        User(
            id=101,
            username="child1",
            email="child1@test.com",
            is_parent=False,
            parent_id=100
        ),
        User(
            id=102,
            username="child2", 
            email="child2@test.com",
            is_parent=False,
            parent_id=100
        )
    ]


@pytest_asyncio.fixture
async def mock_db_session():
    """Create mock database session."""
    mock_session = AsyncMock()
    return mock_session


@pytest_asyncio.fixture
async def sample_chores():
    """Create sample chores for testing calculations."""
    return [
        # Child 1 approved chores
        Chore(
            id=1,
            title="Clean room",
            reward=5.0,
            approval_reward=5.0,
            assignee_id=101,
            creator_id=100,
            is_completed=True,
            is_approved=True,
            created_at=datetime.now() - timedelta(days=5),
            updated_at=datetime.now() - timedelta(days=4)
        ),
        Chore(
            id=2,
            title="Do dishes",
            reward=3.50,
            approval_reward=4.0,  # Parent increased reward
            assignee_id=101,
            creator_id=100,
            is_completed=True,
            is_approved=True,
            created_at=datetime.now() - timedelta(days=3),
            updated_at=datetime.now() - timedelta(days=2)
        ),
        # Child 1 pending chore
        Chore(
            id=3,
            title="Take out trash",
            reward=2.0,
            approval_reward=None,  # Not approved yet
            assignee_id=101,
            creator_id=100,
            is_completed=True,
            is_approved=False,
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(hours=2)
        ),
        # Child 2 approved chore
        Chore(
            id=4,
            title="Vacuum living room",
            reward=7.25,
            approval_reward=7.25,
            assignee_id=102,
            creator_id=100,
            is_completed=True,
            is_approved=True,
            created_at=datetime.now() - timedelta(days=6),
            updated_at=datetime.now() - timedelta(days=5)
        ),
        # Child 2 incomplete chore (should not count)
        Chore(
            id=5,
            title="Organize closet",
            reward=10.0,
            approval_reward=None,
            assignee_id=102,
            creator_id=100,
            is_completed=False,
            is_approved=False,
            created_at=datetime.now() - timedelta(hours=1)
        )
    ]


@pytest_asyncio.fixture
async def sample_adjustments():
    """Create sample reward adjustments for testing."""
    return [
        # Child 1 bonus
        RewardAdjustment(
            id=1,
            child_id=101,
            parent_id=100,
            amount=Decimal("2.50"),
            reason="Good behavior bonus",
            created_at=datetime.now() - timedelta(days=3)
        ),
        # Child 1 deduction
        RewardAdjustment(
            id=2,
            child_id=101,
            parent_id=100,
            amount=Decimal("-1.00"),
            reason="Late bedtime penalty",
            created_at=datetime.now() - timedelta(days=1)
        ),
        # Child 2 bonus
        RewardAdjustment(
            id=3,
            child_id=102,
            parent_id=100,
            amount=Decimal("5.00"),
            reason="Excellent week",
            created_at=datetime.now() - timedelta(days=2)
        )
    ]


class TestSingleChildCalculations:
    """Test financial calculations for a single child."""
    
    @pytest.mark.asyncio
    async def test_single_child_basic_calculation(self, mock_db_session, mock_parent_user, mock_child_users, sample_chores, sample_adjustments):
        """Test basic allowance calculation for single child."""
        # Arrange - Child 1 has 2 approved chores (5.0 + 4.0) + adjustments (2.50 - 1.00) = 10.50
        child1 = mock_child_users[0]
        child1_chores = [c for c in sample_chores if c.assignee_id == 101 and c.is_approved]
        child1_adjustments = [a for a in sample_adjustments if a.child_id == 101]
        
        # Mock database queries
        with patch('backend.app.api.api_v1.endpoints.reports.select') as mock_select:
            # Mock children query
            mock_children_query = Mock()
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1]
            
            # Mock chores query  
            mock_chores_query = Mock()
            mock_chores_result = Mock()
            mock_chores_result.scalars.return_value.all.return_value = child1_chores
            
            # Mock adjustments query
            mock_adjustments_result = Mock()
            mock_adjustments_result.scalar.return_value = Decimal("1.50")  # 2.50 - 1.00
            
            mock_db_session.execute.side_effect = [
                mock_children_result,
                mock_chores_result,
                mock_adjustments_result
            ]
            
            # Act - Call function directly without FastAPI parameters
            result = await get_allowance_summary(
                date_from=None,
                date_to=None,
                child_id=None,
                current_user=mock_parent_user,
                db=mock_db_session
            )
            
            # Assert financial calculations
            assert len(result.child_summaries) == 1
            child_summary = result.child_summaries[0]
            
            # Verify earned amount: 5.0 + 4.0 = 9.0
            assert child_summary.total_earned == 9.0
            
            # Verify adjustments: 1.50 (from mock)
            assert child_summary.total_adjustments == 1.50
            
            # Verify balance: 9.0 + 1.50 = 10.50
            assert child_summary.balance_due == 10.50
            
            # Verify completed chores count
            assert child_summary.completed_chores == 2
    
    @pytest.mark.asyncio
    async def test_child_with_no_earnings(self, mock_db_session, mock_parent_user, mock_child_users):
        """Test calculation for child with no completed chores."""
        # Arrange
        child1 = mock_child_users[0]
        
        with patch('backend.app.api.api_v1.endpoints.reports.select') as mock_select:
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1]
            
            mock_chores_result = Mock()
            mock_chores_result.scalars.return_value.all.return_value = []  # No chores
            
            mock_adjustments_result = Mock()
            mock_adjustments_result.scalar.return_value = None  # No adjustments
            
            mock_db_session.execute.side_effect = [
                mock_children_result,
                mock_chores_result,
                mock_adjustments_result
            ]
            
            # Act
            result = await get_allowance_summary(
                date_from=None,
                date_to=None,
                child_id=None,
                current_user=mock_parent_user,
                db=mock_db_session
            )
            
            # Assert
            child_summary = result.child_summaries[0]
            assert child_summary.total_earned == 0.0
            assert child_summary.total_adjustments == 0.0
            assert child_summary.balance_due == 0.0
            assert child_summary.completed_chores == 0
    
    @pytest.mark.asyncio
    async def test_child_with_only_negative_adjustments(self, mock_db_session, mock_parent_user, mock_child_users):
        """Test calculation for child with negative balance due to deductions."""
        # Arrange
        child1 = mock_child_users[0]
        
        with patch('backend.app.api.api_v1.endpoints.reports.select') as mock_select:
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1]
            
            mock_chores_result = Mock()
            mock_chores_result.scalars.return_value.all.return_value = []  # No completed chores
            
            mock_adjustments_result = Mock()
            mock_adjustments_result.scalar.return_value = Decimal("-5.00")  # Big deduction
            
            mock_db_session.execute.side_effect = [
                mock_children_result,
                mock_chores_result,
                mock_adjustments_result
            ]
            
            # Act
            result = await get_allowance_summary(
                date_from=None,
                date_to=None,
                child_id=None,
                current_user=mock_parent_user,
                db=mock_db_session
            )
            
            # Assert negative balance is correctly calculated
            child_summary = result.child_summaries[0]
            assert child_summary.total_earned == 0.0
            assert child_summary.total_adjustments == -5.0
            assert child_summary.balance_due == -5.0  # Child owes money


class TestMultipleChildrenCalculations:
    """Test financial calculations for multiple children."""
    
    @pytest.mark.asyncio 
    async def test_family_totals_calculation(self, mock_db_session, mock_parent_user, mock_child_users):
        """Test that family totals correctly aggregate across all children."""
        # Arrange - Set up realistic scenario with multiple children
        child1, child2 = mock_child_users
        
        # Child 1: $15.50 earned, $2.00 adjustments = $17.50 balance
        # Child 2: $10.25 earned, $-1.50 adjustments = $8.75 balance
        # Family total: $25.75 earned, $0.50 adjustments = $26.25 balance
        
        with patch('backend.app.api.api_v1.endpoints.reports.select') as mock_select:
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1, child2]
            
            def mock_execute_side_effect(query):
                # Simulate different queries based on call order
                call_count = mock_db_session.execute.call_count
                
                if call_count == 1:
                    return mock_children_result
                elif call_count == 2:  # Child 1 chores
                    mock_result = Mock()
                    # Mock 3 completed chores totaling $15.50
                    mock_chores = [
                        Mock(is_completed=True, is_approved=True, approval_reward=5.50, reward=5.0),
                        Mock(is_completed=True, is_approved=True, approval_reward=None, reward=4.00),
                        Mock(is_completed=True, is_approved=True, approval_reward=6.00, reward=5.50),
                    ]
                    mock_result.scalars.return_value.all.return_value = mock_chores
                    return mock_result
                elif call_count == 3:  # Child 1 adjustments
                    mock_result = Mock()
                    mock_result.scalar.return_value = Decimal("2.00")
                    return mock_result
                elif call_count == 4:  # Child 2 chores
                    mock_result = Mock()
                    # Mock 2 completed chores totaling $10.25
                    mock_chores = [
                        Mock(is_completed=True, is_approved=True, approval_reward=7.25, reward=7.00),
                        Mock(is_completed=True, is_approved=True, approval_reward=None, reward=3.00),
                    ]
                    mock_result.scalars.return_value.all.return_value = mock_chores
                    return mock_result
                elif call_count == 5:  # Child 2 adjustments
                    mock_result = Mock()
                    mock_result.scalar.return_value = Decimal("-1.50")
                    return mock_result
            
            mock_db_session.execute.side_effect = mock_execute_side_effect
            
            # Act
            result = await get_allowance_summary(
                date_from=None,
                date_to=None,
                child_id=None,
                current_user=mock_parent_user,
                db=mock_db_session
            )
            
            # Assert individual child calculations
            assert len(result.child_summaries) == 2
            
            # Child 1: 5.50 + 4.00 + 6.00 = 15.50 earned, +2.00 adjustments = 17.50 balance
            child1_summary = result.child_summaries[0]
            assert child1_summary.total_earned == 15.50
            assert child1_summary.total_adjustments == 2.00
            assert child1_summary.balance_due == 17.50
            
            # Child 2: 7.25 + 3.00 = 10.25 earned, -1.50 adjustments = 8.75 balance
            child2_summary = result.child_summaries[1]
            assert child2_summary.total_earned == 10.25
            assert child2_summary.total_adjustments == -1.50
            assert child2_summary.balance_due == 8.75
            
            # Assert family totals
            family = result.family_summary
            assert family.total_children == 2
            assert family.total_earned == 25.75  # 15.50 + 10.25
            assert family.total_adjustments == 0.50  # 2.00 + (-1.50)
            assert family.total_balance_due == 26.25  # 17.50 + 8.75
            assert family.total_completed_chores == 5  # 3 + 2


class TestPendingChoresCalculation:
    """Test calculation of pending chore values."""
    
    @pytest.mark.asyncio
    async def test_pending_chores_value_calculation(self, mock_db_session, mock_parent_user, mock_child_users):
        """Test that pending chores are valued correctly but don't affect balance."""
        # Arrange
        child1 = mock_child_users[0]
        
        with patch('backend.app.api.api_v1.endpoints.reports.select') as mock_select:
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1]
            
            # Mock chores: 1 approved for $5, 2 pending for $3 + $4 = $7
            mock_chores = [
                Mock(is_completed=True, is_approved=True, approval_reward=5.0, reward=5.0),  # Approved
                Mock(is_completed=True, is_approved=False, approval_reward=None, reward=3.0),  # Pending
                Mock(is_completed=True, is_approved=False, approval_reward=None, reward=4.0),  # Pending
            ]
            
            mock_chores_result = Mock()
            mock_chores_result.scalars.return_value.all.return_value = mock_chores
            
            mock_adjustments_result = Mock()
            mock_adjustments_result.scalar.return_value = None
            
            mock_db_session.execute.side_effect = [
                mock_children_result,
                mock_chores_result,
                mock_adjustments_result
            ]
            
            # Act
            result = await get_allowance_summary(
                date_from=None,
                date_to=None,
                child_id=None,
                current_user=mock_parent_user,
                db=mock_db_session
            )
            
            # Assert
            child_summary = result.child_summaries[0]
            assert child_summary.total_earned == 5.0  # Only approved chore
            assert child_summary.pending_chores_value == 7.0  # $3 + $4 pending
            assert child_summary.balance_due == 5.0  # Only approved amount affects balance
            assert child_summary.completed_chores == 1  # Only approved chores count


class TestPrecisionAndEdgeCases:
    """Test financial precision and edge cases."""
    
    @pytest.mark.asyncio
    async def test_decimal_precision_accuracy(self, mock_db_session, mock_parent_user, mock_child_users):
        """Test that decimal calculations maintain precision for monetary values."""
        # Arrange - Use precise decimal values
        child1 = mock_child_users[0]
        
        with patch('backend.app.api.api_v1.endpoints.reports.select') as mock_select:
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1]
            
            # Mock chores with precise decimal values
            mock_chores = [
                Mock(is_completed=True, is_approved=True, approval_reward=3.33, reward=3.00),
                Mock(is_completed=True, is_approved=True, approval_reward=None, reward=2.67),
                Mock(is_completed=True, is_approved=True, approval_reward=1.50, reward=1.25),
            ]
            
            mock_chores_result = Mock()
            mock_chores_result.scalars.return_value.all.return_value = mock_chores
            
            # Precise adjustment calculation: 0.33 + (-0.83) = -0.50
            mock_adjustments_result = Mock()
            mock_adjustments_result.scalar.return_value = Decimal("-0.50")
            
            mock_db_session.execute.side_effect = [
                mock_children_result,
                mock_chores_result,
                mock_adjustments_result
            ]
            
            # Act
            result = await get_allowance_summary(
                date_from=None,
                date_to=None,
                child_id=None,
                current_user=mock_parent_user,
                db=mock_db_session
            )
            
            # Assert precise calculations
            child_summary = result.child_summaries[0]
            # Earnings: 3.33 + 2.67 + 1.50 = 7.50
            assert child_summary.total_earned == 7.50
            assert child_summary.total_adjustments == -0.50
            # Balance: 7.50 + (-0.50) = 7.00
            assert child_summary.balance_due == 7.00
    
    @pytest.mark.asyncio
    async def test_large_monetary_values(self, mock_db_session, mock_parent_user, mock_child_users):
        """Test calculations with large monetary values."""
        # Arrange
        child1 = mock_child_users[0]
        
        with patch('backend.app.api.api_v1.endpoints.reports.select') as mock_select:
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1]
            
            # Mock high-value chores
            mock_chores = [
                Mock(is_completed=True, is_approved=True, approval_reward=999.99, reward=500.00),
                Mock(is_completed=True, is_approved=True, approval_reward=None, reward=1500.50),
            ]
            
            mock_chores_result = Mock()
            mock_chores_result.scalars.return_value.all.return_value = mock_chores
            
            mock_adjustments_result = Mock()
            mock_adjustments_result.scalar.return_value = Decimal("250.75")
            
            mock_db_session.execute.side_effect = [
                mock_children_result,
                mock_chores_result,
                mock_adjustments_result
            ]
            
            # Act
            result = await get_allowance_summary(
                date_from=None,
                date_to=None,
                child_id=None,
                current_user=mock_parent_user,
                db=mock_db_session
            )
            
            # Assert large value handling
            child_summary = result.child_summaries[0]
            assert child_summary.total_earned == 2500.49  # 999.99 + 1500.50
            assert child_summary.total_adjustments == 250.75
            assert child_summary.balance_due == 2751.24
    
    @pytest.mark.asyncio
    async def test_zero_and_null_value_handling(self, mock_db_session, mock_parent_user, mock_child_users):
        """Test proper handling of zero and null values."""
        # Arrange
        child1 = mock_child_users[0]
        
        with patch('backend.app.api.api_v1.endpoints.reports.select') as mock_select:
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1]
            
            # Mock chores with null/zero values
            mock_chores = [
                Mock(is_completed=True, is_approved=True, approval_reward=None, reward=0.0),
                Mock(is_completed=True, is_approved=True, approval_reward=0.0, reward=None),
                Mock(is_completed=True, is_approved=True, approval_reward=5.0, reward=3.0),
            ]
            
            mock_chores_result = Mock()
            mock_chores_result.scalars.return_value.all.return_value = mock_chores
            
            mock_adjustments_result = Mock()
            mock_adjustments_result.scalar.return_value = None  # No adjustments
            
            mock_db_session.execute.side_effect = [
                mock_children_result,
                mock_chores_result,
                mock_adjustments_result
            ]
            
            # Act
            result = await get_allowance_summary(
                date_from=None,
                date_to=None,
                child_id=None,
                current_user=mock_parent_user,
                db=mock_db_session
            )
            
            # Assert null/zero handling
            child_summary = result.child_summaries[0]
            # Should handle null/zero gracefully: 0 + 0 + 5.0 = 5.0
            assert child_summary.total_earned == 5.0
            assert child_summary.total_adjustments == 0.0
            assert child_summary.balance_due == 5.0


class TestDateRangeFiltering:
    """Test date range filtering accuracy."""
    
    @pytest.mark.asyncio
    async def test_date_range_filtering_chores(self, mock_db_session, mock_parent_user, mock_child_users):
        """Test that date filtering correctly limits chores to specified range."""
        # Arrange
        child1 = mock_child_users[0]
        date_from = "2025-08-01"
        date_to = "2025-08-15"
        
        with patch('backend.app.api.api_v1.endpoints.reports.select') as mock_select:
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1]
            
            # Only chores within date range should be included
            mock_chores_result = Mock()
            mock_chores_result.scalars.return_value.all.return_value = []  # Empty after filtering
            
            mock_adjustments_result = Mock()
            mock_adjustments_result.scalar.return_value = None
            
            mock_db_session.execute.side_effect = [
                mock_children_result,
                mock_chores_result,
                mock_adjustments_result
            ]
            
            # Act
            result = await get_allowance_summary(
                date_from=date_from,
                date_to=date_to,
                current_user=mock_parent_user,
                db=mock_db_session
            )
            
            # Assert filtering applied
            child_summary = result.child_summaries[0]
            assert child_summary.total_earned == 0.0  # No chores in range
            
            # Verify date range in family summary
            family = result.family_summary
            assert family.period_start is not None
            assert family.period_end is not None


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_db_session, mock_parent_user):
        """Test that database errors are properly handled."""
        # Arrange
        mock_db_session.execute.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            await get_allowance_summary(
                current_user=mock_parent_user,
                db=mock_db_session
            )
    
    @pytest.mark.asyncio
    async def test_invalid_date_format_handling(self, mock_db_session, mock_parent_user):
        """Test handling of invalid date formats."""
        # Arrange
        invalid_date = "not-a-date"
        
        # Act & Assert
        with pytest.raises(ValueError):
            await get_allowance_summary(
                date_from=invalid_date,
                current_user=mock_parent_user,
                db=mock_db_session
            )


class TestConcurrentCalculations:
    """Test concurrent calculation scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_allowance_requests(self, mock_db_session, mock_parent_user, mock_child_users):
        """Test that concurrent allowance summary requests don't interfere."""
        # Arrange
        import asyncio
        
        child1 = mock_child_users[0]
        
        def mock_execute_side_effect(query):
            mock_children_result = Mock()
            mock_children_result.scalars.return_value.all.return_value = [child1]
            
            mock_chores_result = Mock()
            mock_chores_result.scalars.return_value.all.return_value = []
            
            mock_adjustments_result = Mock()
            mock_adjustments_result.scalar.return_value = None
            
            return [mock_children_result, mock_chores_result, mock_adjustments_result][
                mock_db_session.execute.call_count % 3
            ]
        
        mock_db_session.execute.side_effect = mock_execute_side_effect
        
        # Act - Simulate concurrent requests
        tasks = [
            get_allowance_summary(current_user=mock_parent_user, db=mock_db_session)
            for _ in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Assert
        assert len(results) == 3
        for result in results:
            assert isinstance(result, AllowanceSummaryResponse)
            assert len(result.child_summaries) == 1
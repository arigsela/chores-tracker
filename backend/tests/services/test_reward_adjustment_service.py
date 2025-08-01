import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException

from backend.app.services.reward_adjustment_service import RewardAdjustmentService
from backend.app.models.user import User
from backend.app.models.reward_adjustment import RewardAdjustment
from backend.app.schemas.reward_adjustment import RewardAdjustmentCreate


class TestRewardAdjustmentService:
    """Test cases for RewardAdjustmentService business logic."""

    @pytest.fixture
    def service(self):
        """Create RewardAdjustmentService instance."""
        return RewardAdjustmentService()

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def parent_user(self):
        """Sample parent user for testing."""
        user = Mock(spec=User)
        user.id = 1
        user.username = "parent1"
        user.is_parent = True
        return user

    @pytest.fixture
    def child_user(self):
        """Sample child user for testing."""
        user = Mock(spec=User)
        user.id = 2
        user.username = "child1"
        user.is_parent = False
        user.parent_id = 1
        return user

    @pytest.fixture
    def adjustment_data(self):
        """Sample adjustment data for testing."""
        return RewardAdjustmentCreate(
            child_id=2,
            amount=Decimal("10.00"),
            reason="Good behavior bonus"
        )

    # Authorization Tests
    @pytest.mark.asyncio
    async def test_create_adjustment_parent_only(self, service, mock_db, child_user, adjustment_data):
        """Test that only parents can create adjustments."""
        with patch.object(service.user_repository, 'get', return_value=child_user):
            with pytest.raises(HTTPException) as exc_info:
                await service.create_adjustment(
                    mock_db,
                    adjustment_data=adjustment_data,
                    current_user_id=child_user.id
                )
            assert exc_info.value.status_code == 403
            assert "Only parents can create reward adjustments" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_adjustment_parent_success(
        self, service, mock_db, parent_user, child_user, adjustment_data
    ):
        """Test successful adjustment creation by parent."""
        created_adjustment = Mock(spec=RewardAdjustment)
        created_adjustment.id = 1
        created_adjustment.parent_id = parent_user.id
        created_adjustment.child_id = adjustment_data.child_id
        created_adjustment.amount = adjustment_data.amount
        created_adjustment.reason = adjustment_data.reason
        created_adjustment.created_at = datetime.utcnow()
        
        with patch.object(service.user_repository, 'get') as mock_get_user:
            mock_get_user.side_effect = [parent_user, child_user]  # First call returns parent, second returns child
            
            with patch.object(service.repository, 'calculate_total_adjustments', return_value=Decimal("50.00")):
                with patch.object(service.repository, 'create', return_value=created_adjustment):
                    result = await service.create_adjustment(
                        mock_db,
                        adjustment_data=adjustment_data,
                        current_user_id=parent_user.id
                    )
                    
                    assert result.id == 1
                    assert result.parent_id == parent_user.id
                    assert result.amount == Decimal("10.00")

    # Validation Tests
    @pytest.mark.asyncio
    async def test_create_adjustment_child_not_found(
        self, service, mock_db, parent_user, adjustment_data
    ):
        """Test adjustment creation fails when child doesn't exist."""
        with patch.object(service.user_repository, 'get') as mock_get_user:
            mock_get_user.side_effect = [parent_user, None]  # Parent exists, child doesn't
            
            with pytest.raises(HTTPException) as exc_info:
                await service.create_adjustment(
                    mock_db,
                    adjustment_data=adjustment_data,
                    current_user_id=parent_user.id
                )
            assert exc_info.value.status_code == 404
            assert "Child user not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_adjustment_wrong_parent(
        self, service, mock_db, parent_user, adjustment_data
    ):
        """Test adjustment creation fails when child belongs to different parent."""
        other_child = Mock(spec=User)
        other_child.id = 3
        other_child.is_parent = False
        other_child.parent_id = 999  # Different parent
        
        with patch.object(service.user_repository, 'get') as mock_get_user:
            mock_get_user.side_effect = [parent_user, other_child]
            
            with pytest.raises(HTTPException) as exc_info:
                await service.create_adjustment(
                    mock_db,
                    adjustment_data=RewardAdjustmentCreate(
                        child_id=3,
                        amount=Decimal("10.00"),
                        reason="Test"
                    ),
                    current_user_id=parent_user.id
                )
            assert exc_info.value.status_code == 403
            assert "can only adjust rewards for your own children" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_adjustment_zero_amount(self, service, mock_db, parent_user):
        """Test that zero amount adjustments are rejected."""
        with pytest.raises(ValueError) as exc_info:
            adjustment_data = RewardAdjustmentCreate(
                child_id=2,
                amount=Decimal("0.00"),
                reason="Test"
            )
        assert "cannot be zero" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_adjustment_exceeds_max(self, service, mock_db, parent_user):
        """Test that adjustments exceeding max amount are rejected."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            adjustment_data = RewardAdjustmentCreate(
                child_id=2,
                amount=Decimal("1001.00"),
                reason="Test"
            )
        assert "less than or equal to 999.99" in str(exc_info.value).lower()

    # Business Logic Tests
    @pytest.mark.asyncio
    async def test_create_adjustment_prevents_negative_balance(
        self, service, mock_db, parent_user, child_user
    ):
        """Test that adjustments preventing negative balance are rejected."""
        with patch.object(service.user_repository, 'get') as mock_get_user:
            mock_get_user.side_effect = [parent_user, child_user]
            
            # Child has $20 balance
            with patch.object(service.repository, 'calculate_total_adjustments', return_value=Decimal("20.00")):
                # Try to deduct $30
                adjustment_data = RewardAdjustmentCreate(
                    child_id=2,
                    amount=Decimal("-30.00"),
                    reason="Penalty"
                )
                
                with pytest.raises(HTTPException) as exc_info:
                    await service.create_adjustment(
                        mock_db,
                        adjustment_data=adjustment_data,
                        current_user_id=parent_user.id
                    )
                assert exc_info.value.status_code == 400
                assert "would result in negative balance" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_adjustment_allows_negative_with_balance(
        self, service, mock_db, parent_user, child_user
    ):
        """Test that negative adjustments are allowed with sufficient balance."""
        created_adjustment = Mock(spec=RewardAdjustment)
        created_adjustment.id = 1
        created_adjustment.amount = Decimal("-30.00")
        created_adjustment.parent_id = parent_user.id
        created_adjustment.child_id = child_user.id
        created_adjustment.reason = "Penalty for breaking rules"
        created_adjustment.created_at = datetime.utcnow()
        
        with patch.object(service.user_repository, 'get') as mock_get_user:
            mock_get_user.side_effect = [parent_user, child_user]
            
            # Child has $50 balance
            with patch.object(service.repository, 'calculate_total_adjustments', return_value=Decimal("50.00")):
                with patch.object(service.repository, 'create', return_value=created_adjustment):
                    # Deduct $30
                    adjustment_data = RewardAdjustmentCreate(
                        child_id=2,
                        amount=Decimal("-30.00"),
                        reason="Penalty for breaking rules"
                    )
                    
                    result = await service.create_adjustment(
                        mock_db,
                        adjustment_data=adjustment_data,
                        current_user_id=parent_user.id
                    )
                    
                    assert result.amount == Decimal("-30.00")

    # Get Adjustments Tests
    @pytest.mark.asyncio
    async def test_get_adjustments_for_child_parent_access(
        self, service, mock_db, parent_user, child_user
    ):
        """Test parent can get child's adjustments."""
        adjustments = [Mock() for _ in range(3)]
        
        with patch.object(service.user_repository, 'get') as mock_get_user:
            # Return parent first, then child
            mock_get_user.side_effect = [parent_user, child_user]
            
            with patch.object(service.repository, 'get_by_child_id', return_value=adjustments):
                result = await service.get_child_adjustments(
                    mock_db,
                    child_id=child_user.id,
                    current_user_id=parent_user.id
                )
                assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_adjustments_for_child_own_access_denied(
        self, service, mock_db, child_user
    ):
        """Test child cannot get own adjustments (MVP restriction)."""
        with patch.object(service.user_repository, 'get', return_value=child_user):
            with pytest.raises(HTTPException) as exc_info:
                await service.get_child_adjustments(
                    mock_db,
                    child_id=child_user.id,
                    current_user_id=child_user.id
                )
            assert exc_info.value.status_code == 403
            assert "Children cannot view reward adjustments" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_adjustments_for_child_unauthorized(
        self, service, mock_db, child_user
    ):
        """Test child cannot get other child's adjustments."""
        with patch.object(service.user_repository, 'get', return_value=child_user):
            with pytest.raises(HTTPException) as exc_info:
                await service.get_child_adjustments(
                    mock_db,
                    child_id=999,  # Different child
                    current_user_id=child_user.id
                )
            assert exc_info.value.status_code == 403
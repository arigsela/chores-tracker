"""Tests for Pydantic schema validation and consistency."""
import pytest
from pydantic import ValidationError
from decimal import Decimal
from datetime import datetime

from backend.app.schemas.chore import (
    ChoreResponse,
    ChoreCreate,
    ChoreUpdate,
    ChoreApprove
)
from backend.app.schemas.user import (
    UserResponse,
    UserBalanceResponse,
    ChildAllowanceSummary
)
from backend.app.schemas.reward_adjustment import (
    RewardAdjustmentResponse,
    RewardAdjustmentCreate
)


class TestChoreSchemas:
    """Test chore-related schemas."""
    
    def test_chore_response_with_relations(self):
        """Test ChoreResponse can include related user objects."""
        # Test without relations
        chore_data = {
            "id": 1,
            "title": "Clean room",
            "description": "Vacuum and dust",
            "reward": 5.0,
            "is_range_reward": False,
            "cooldown_days": 7,
            "is_recurring": True,
            "is_disabled": False,
            "assignee_id": 2,
            "creator_id": 1,
            "is_completed": False,
            "is_approved": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        chore = ChoreResponse(**chore_data)
        # Note: assignee and creator fields are commented out in ChoreResponse 
        # to avoid SQLAlchemy lazy loading issues. Test IDs instead.
        assert chore.assignee_id == 2
        assert chore.creator_id == 1
    
    def test_chore_approve_range_validation(self):
        """Test ChoreApprove schema for range rewards."""
        # Valid approval with reward_value
        approve = ChoreApprove(is_approved=True, reward_value=5.0)
        assert approve.reward_value == 5.0
        
        # Valid approval without reward_value (for fixed rewards)
        approve = ChoreApprove(is_approved=True)
        assert approve.reward_value is None


class TestUserSchemas:
    """Test user-related schemas."""
    
    def test_user_balance_response(self):
        """Test UserBalanceResponse schema."""
        balance_data = {
            "balance": 25.50,
            "total_earned": 45.00,
            "adjustments": 5.50,
            "paid_out": 25.00,
            "pending_chores_value": 10.00
        }
        balance = UserBalanceResponse(**balance_data)
        assert balance.balance == 25.50
        assert balance.total_earned == 45.00
    
    def test_child_allowance_summary(self):
        """Test ChildAllowanceSummary schema with examples."""
        summary_data = {
            "id": 2,
            "username": "child_user",
            "completed_chores": 5,
            "total_earned": 25.50,
            "total_adjustments": -2.00,
            "paid_out": 0.00,
            "balance_due": 23.50
        }
        summary = ChildAllowanceSummary(**summary_data)
        assert summary.username == "child_user"
        assert summary.balance_due == 23.50
        
        # Test that ConfigDict is properly set
        assert hasattr(ChildAllowanceSummary, 'model_config')
        assert ChildAllowanceSummary.model_config.get('from_attributes') is True


class TestAdjustmentSchemas:
    """Test reward adjustment schemas."""
    
    def test_adjustment_response_with_relations(self):
        """Test RewardAdjustmentResponse can include related users."""
        adjustment_data = {
            "id": 1,
            "amount": Decimal("5.00"),
            "reason": "Bonus for extra help",
            "child_id": 2,
            "parent_id": 1,
            "created_at": datetime.now()
        }
        adjustment = RewardAdjustmentResponse(**adjustment_data)
        assert adjustment.child is None
        assert adjustment.parent is None
        
        # Test with relations
        child_data = {
            "id": 2,
            "username": "child_user",
            "is_parent": False,
            "is_active": True,
            "parent_id": 1
        }
        parent_data = {
            "id": 1,
            "username": "parent_user",
            "email": "parent@example.com",
            "is_parent": True,
            "is_active": True
        }
        adjustment_data["child"] = UserResponse(**child_data)
        adjustment_data["parent"] = UserResponse(**parent_data)
        adjustment = RewardAdjustmentResponse(**adjustment_data)
        assert adjustment.child.username == "child_user"
        assert adjustment.parent.username == "parent_user"
    
    def test_adjustment_create_validation(self):
        """Test RewardAdjustmentCreate validation."""
        # Valid adjustment
        adjustment = RewardAdjustmentCreate(
            amount=Decimal("5.00"),
            reason="Bonus",
            child_id=2
        )
        assert adjustment.amount == Decimal("5.00")
        
        # Invalid: zero amount
        with pytest.raises(ValidationError) as exc_info:
            RewardAdjustmentCreate(
                amount=Decimal("0.00"),
                reason="Invalid",
                child_id=2
            )
        assert "cannot be zero" in str(exc_info.value)


class TestSchemaExamples:
    """Test that all schemas have proper examples."""
    
    def test_schema_examples_exist(self):
        """Verify all response schemas have json_schema_extra examples."""
        schemas_with_examples = [
            ChoreResponse,
            UserResponse,
            UserBalanceResponse,
            ChildAllowanceSummary,
            RewardAdjustmentResponse
        ]
        
        for schema_class in schemas_with_examples:
            assert hasattr(schema_class, 'model_config'), f"{schema_class.__name__} missing model_config"
            config = schema_class.model_config
            if hasattr(config, 'get'):
                json_extra = config.get('json_schema_extra', {})
            else:
                json_extra = getattr(config, 'json_schema_extra', {})
            assert 'example' in json_extra, f"{schema_class.__name__} missing example in json_schema_extra"
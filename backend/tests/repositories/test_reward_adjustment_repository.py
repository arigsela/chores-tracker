import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from backend.app.models.user import User
from backend.app.models.reward_adjustment import RewardAdjustment
from backend.app.repositories.reward_adjustment import RewardAdjustmentRepository


class TestRewardAdjustmentRepository:
    """Test cases for RewardAdjustmentRepository."""

    @pytest.fixture
    def repo(self):
        """Create RewardAdjustmentRepository instance."""
        return RewardAdjustmentRepository()

    # Basic CRUD Tests
    @pytest.mark.asyncio
    async def test_create_reward_adjustment(self, db_session, repo, test_parent_user, test_child_user):
        """Test creating a new reward adjustment."""
        adjustment_data = {
            "parent_id": test_parent_user.id,
            "child_id": test_child_user.id,
            "amount": Decimal("25.00"),
            "reason": "Good behavior bonus"
        }
        
        created = await repo.create(db_session, obj_in=adjustment_data)
        
        assert created.id is not None
        assert created.parent_id == test_parent_user.id
        assert created.child_id == test_child_user.id
        assert created.amount == Decimal("25.00")
        assert created.reason == "Good behavior bonus"
        assert created.created_at is not None

    @pytest.mark.asyncio
    async def test_get_adjustment_by_id(self, db_session, repo, test_reward_adjustment):
        """Test retrieving adjustment by ID."""
        found = await repo.get(db_session, id=test_reward_adjustment.id)
        
        assert found is not None
        assert found.id == test_reward_adjustment.id
        assert found.amount == test_reward_adjustment.amount

    @pytest.mark.asyncio
    async def test_get_adjustments_by_child(self, db_session, repo, test_parent_user, test_child_user):
        """Test retrieving adjustments by child ID."""
        # Create multiple adjustments
        for i in range(5):
            adjustment = RewardAdjustment(
                parent_id=test_parent_user.id,
                child_id=test_child_user.id,
                amount=Decimal(f"{i+1}.00"),
                reason=f"Test adjustment {i+1}"
            )
            db_session.add(adjustment)
        await db_session.commit()
        
        # Get adjustments
        adjustments = await repo.get_by_child_id(
            db_session, 
            child_id=test_child_user.id,
            limit=10
        )
        
        assert len(adjustments) == 5
        # Check all expected amounts are present
        amounts = {adj.amount for adj in adjustments}
        expected_amounts = {Decimal(f"{i+1}.00") for i in range(5)}
        assert amounts == expected_amounts

    # Balance Calculation Tests
    @pytest.mark.asyncio
    async def test_calculate_total_adjustments_sum(self, db_session, repo, test_parent_user, test_child_user):
        """Test balance calculation sums all adjustments."""
        # Create mixed adjustments
        adjustments_data = [
            (Decimal("10.00"), "Bonus 1"),
            (Decimal("5.00"), "Bonus 2"),
            (Decimal("-3.00"), "Penalty 1"),
            (Decimal("7.50"), "Bonus 3"),
            (Decimal("-2.00"), "Penalty 2")
        ]
        
        for amount, reason in adjustments_data:
            adjustment = RewardAdjustment(
                parent_id=test_parent_user.id,
                child_id=test_child_user.id,
                amount=amount,
                reason=reason
            )
            db_session.add(adjustment)
        await db_session.commit()
        
        # Calculate total
        total = await repo.calculate_total_adjustments(db_session, child_id=test_child_user.id)
        
        # 10 + 5 - 3 + 7.50 - 2 = 17.50
        assert total == Decimal("17.50")

    @pytest.mark.asyncio
    async def test_calculate_total_adjustments_no_history(self, db_session, repo, test_child_user):
        """Test balance calculation with no adjustments."""
        total = await repo.calculate_total_adjustments(db_session, child_id=test_child_user.id)
        assert total == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_get_adjustment_count(self, db_session, repo, test_parent_user, test_child_user):
        """Test getting count of adjustments."""
        # Create 3 adjustments
        for i in range(3):
            adjustment = RewardAdjustment(
                parent_id=test_parent_user.id,
                child_id=test_child_user.id,
                amount=Decimal("5.00"),
                reason=f"Test {i}"
            )
            db_session.add(adjustment)
        await db_session.commit()
        
        count = await repo.get_adjustment_count(db_session, child_id=test_child_user.id)
        assert count == 3

    # Advanced Query Tests
    @pytest.mark.asyncio
    async def test_get_adjustments_by_parent(self, db_session, repo, test_parent_user):
        """Test retrieving adjustments by parent ID."""
        # Create child users
        child1 = User(username="repochild1", email="rc1@test.com", hashed_password="h", 
                     is_parent=False, parent_id=test_parent_user.id)
        child2 = User(username="repochild2", email="rc2@test.com", hashed_password="h", 
                     is_parent=False, parent_id=test_parent_user.id)
        db_session.add_all([child1, child2])
        await db_session.commit()
        
        # Create adjustments for both children
        adj1 = RewardAdjustment(parent_id=test_parent_user.id, child_id=child1.id, 
                               amount=Decimal("10.00"), reason="Child 1 bonus")
        adj2 = RewardAdjustment(parent_id=test_parent_user.id, child_id=child2.id, 
                               amount=Decimal("15.00"), reason="Child 2 bonus")
        db_session.add_all([adj1, adj2])
        await db_session.commit()
        
        # Get all adjustments by parent
        adjustments = await repo.get_by_parent(db_session, parent_id=test_parent_user.id)
        assert len(adjustments) == 2

    @pytest.mark.asyncio
    async def test_get_adjustments_with_pagination(self, db_session, repo, test_parent_user, test_child_user):
        """Test pagination with limit and offset."""
        # Create 10 adjustments
        for i in range(10):
            adjustment = RewardAdjustment(
                parent_id=test_parent_user.id,
                child_id=test_child_user.id,
                amount=Decimal(f"{i+1}.00"),
                reason=f"Test {i+1}"
            )
            db_session.add(adjustment)
        await db_session.commit()
        
        # Get first page (5 items)
        page1 = await repo.get_by_child_id(db_session, child_id=test_child_user.id, limit=5, skip=0)
        assert len(page1) == 5
        
        # Get second page
        page2 = await repo.get_by_child_id(db_session, child_id=test_child_user.id, limit=5, skip=5)
        assert len(page2) == 5
        
        # Verify no overlap
        page1_ids = {adj.id for adj in page1}
        page2_ids = {adj.id for adj in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

    @pytest.mark.asyncio
    async def test_negative_balance_calculation(self, db_session, repo, test_parent_user, test_child_user):
        """Test balance calculation with net negative result."""
        # Create adjustments resulting in negative balance
        adj1 = RewardAdjustment(parent_id=test_parent_user.id, child_id=test_child_user.id,
                               amount=Decimal("10.00"), reason="Initial bonus")
        adj2 = RewardAdjustment(parent_id=test_parent_user.id, child_id=test_child_user.id,
                               amount=Decimal("-25.00"), reason="Large penalty")
        db_session.add_all([adj1, adj2])
        await db_session.commit()
        
        total = await repo.calculate_total_adjustments(db_session, child_id=test_child_user.id)
        assert total == Decimal("-15.00")

    @pytest.mark.asyncio
    async def test_large_decimal_precision(self, db_session, repo, test_parent_user, test_child_user):
        """Test handling of decimal precision."""
        # Create adjustment with cents
        adjustment = RewardAdjustment(
            parent_id=test_parent_user.id,
            child_id=test_child_user.id,
            amount=Decimal("12.99"),
            reason="Precise amount"
        )
        db_session.add(adjustment)
        await db_session.commit()
        
        total = await repo.calculate_total_adjustments(db_session, child_id=test_child_user.id)
        assert total == Decimal("12.99")
        assert str(total) == "12.99"  # Verify precision maintained
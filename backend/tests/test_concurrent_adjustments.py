import pytest
import asyncio
import os
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.models.reward_adjustment import RewardAdjustment
from backend.app.repositories.reward_adjustment import RewardAdjustmentRepository
from backend.app.services.reward_adjustment_service import RewardAdjustmentService
from backend.app.schemas.reward_adjustment import RewardAdjustmentCreate
from backend.app.db.base import get_db
from fastapi import HTTPException

# Skip these tests in CI environment due to SQLite limitations
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Concurrent tests not compatible with SQLite in CI"
)


class TestConcurrentAdjustments:
    """Test cases for concurrent adjustment handling."""

    @pytest.fixture
    async def parent_user(self, db_session: AsyncSession):
        """Create a parent user."""
        user = User(
            username="concurrentparent",
            email="concurrent@test.com",
            hashed_password="hashed",
            is_parent=True,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def child_user(self, db_session: AsyncSession, parent_user):
        """Create a child user with initial balance."""
        user = User(
            username="concurrentchild",
            email="concurrentchild@test.com",
            hashed_password="hashed",
            is_parent=False,
            is_active=True,
            parent_id=parent_user.id
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Add initial balance
        initial_adjustment = RewardAdjustment(
            parent_id=parent_user.id,
            child_id=user.id,
            amount=Decimal("100.00"),
            reason="Initial balance for testing"
        )
        db_session.add(initial_adjustment)
        await db_session.commit()
        
        return user

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_adjustments_same_child(
        self, db_session: AsyncSession, parent_user, child_user
    ):
        """Test multiple concurrent adjustments to the same child."""
        service = RewardAdjustmentService()
        
        async def create_adjustment(amount: Decimal, reason: str):
            """Helper to create an adjustment."""
            adjustment_data = RewardAdjustmentCreate(
                child_id=child_user.id,
                amount=amount,
                reason=reason
            )
            try:
                result = await service.create_adjustment(
                    db=db_session,
                    adjustment_data=adjustment_data,
                    current_user_id=parent_user.id
                )
                return result
            except HTTPException:
                # Expected for some concurrent operations
                return None

        # Create 10 concurrent adjustments of -$15 each
        # With initial balance of $100, only 6 should succeed
        tasks = []
        for i in range(10):
            task = create_adjustment(Decimal("-15.00"), f"Concurrent penalty {i+1}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful adjustments
        successful = [r for r in results if r is not None and not isinstance(r, Exception)]
        failed = [r for r in results if r is None or isinstance(r, HTTPException)]
        
        # Verify final balance is not negative
        repo = RewardAdjustmentRepository()
        final_balance = await repo.calculate_total_adjustments(db_session, child_id=child_user.id)
        assert final_balance >= Decimal("0.00")
        
        # At least some should succeed, some should fail
        assert len(successful) > 0
        assert len(failed) > 0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_balance_queries(
        self, db_session: AsyncSession, parent_user, child_user
    ):
        """Test concurrent balance queries during adjustments."""
        service = RewardAdjustmentService()
        repo = RewardAdjustmentRepository()
        
        async def query_balance():
            """Helper to query balance."""
            return await repo.calculate_total_adjustments(db_session, child_id=child_user.id)
        
        async def create_adjustment():
            """Helper to create an adjustment."""
            adjustment_data = RewardAdjustmentCreate(
                child_id=child_user.id,
                amount=Decimal("5.00"),
                reason="Concurrent test bonus"
            )
            return await service.create_adjustment(
                db=db_session,
                adjustment_data=adjustment_data,
                current_user_id=parent_user.id
            )
        
        # Mix balance queries with adjustments
        tasks = []
        for i in range(20):
            if i % 2 == 0:
                tasks.append(query_balance())
            else:
                tasks.append(create_adjustment())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete without errors
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0
        
        # Final balance should be initial 100 + (10 adjustments * 5)
        final_balance = await query_balance()
        assert final_balance == Decimal("150.00")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_multiple_parents_different_children(
        self, db_session: AsyncSession
    ):
        """Test multiple parents adjusting different children concurrently."""
        # Create multiple parent-child pairs
        parent_child_pairs = []
        for i in range(3):
            parent = User(
                username=f"parent{i}",
                email=f"parent{i}@test.com",
                hashed_password="hashed",
                is_parent=True,
                is_active=True
            )
            db_session.add(parent)
            await db_session.commit()
            
            child = User(
                username=f"child{i}",
                email=f"child{i}@test.com",
                hashed_password="hashed",
                is_parent=False,
                is_active=True,
                parent_id=parent.id
            )
            db_session.add(child)
            await db_session.commit()
            
            parent_child_pairs.append((parent, child))
        
        service = RewardAdjustmentService()
        
        async def adjust_child_balance(parent: User, child: User, index: int):
            """Helper to create adjustments for a specific parent-child pair."""
            tasks = []
            for j in range(5):
                adjustment_data = RewardAdjustmentCreate(
                    child_id=child.id,
                    amount=Decimal("10.00"),
                    reason=f"Parent {index} adjustment {j+1}"
                )
                task = service.create_adjustment(
                    db=db_session,
                    adjustment_data=adjustment_data,
                    current_user_id=parent.id
                )
                tasks.append(task)
            return await asyncio.gather(*tasks)
        
        # Each parent makes 5 adjustments to their child concurrently
        all_tasks = []
        for i, (parent, child) in enumerate(parent_child_pairs):
            task = adjust_child_balance(parent, child, i)
            all_tasks.append(task)
        
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # All should succeed (no conflicts between different children)
        for result_group in results:
            assert not isinstance(result_group, Exception)
            assert len(result_group) == 5
        
        # Verify each child has correct balance
        repo = RewardAdjustmentRepository()
        for _, child in parent_child_pairs:
            balance = await repo.calculate_total_adjustments(db_session, child_id=child.id)
            assert balance == Decimal("50.00")  # 5 adjustments * $10

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rapid_sequential_adjustments(
        self, db_session: AsyncSession, parent_user, child_user
    ):
        """Test rapid sequential adjustments to ensure consistency."""
        service = RewardAdjustmentService()
        repo = RewardAdjustmentRepository()
        
        # Make 20 rapid adjustments
        adjustment_amounts = []
        for i in range(20):
            amount = Decimal(f"{(i % 10) + 1}.00")
            if i % 3 == 0:
                amount = -amount  # Mix in some penalties
            adjustment_amounts.append(amount)
            
            adjustment_data = RewardAdjustmentCreate(
                child_id=child_user.id,
                amount=amount,
                reason=f"Rapid adjustment {i+1}"
            )
            
            await service.create_adjustment(
                db=db_session,
                adjustment_data=adjustment_data,
                current_user_id=parent_user.id
            )
        
        # Calculate expected balance
        expected_balance = Decimal("100.00")  # Initial balance
        for amount in adjustment_amounts:
            expected_balance += amount
        
        # Verify actual balance matches expected
        actual_balance = await repo.calculate_total_adjustments(
            db_session, 
            child_id=child_user.id
        )
        assert actual_balance == expected_balance

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_negative_balance_prevention(
        self, db_session: AsyncSession, parent_user
    ):
        """Test that negative balance prevention works under concurrent load."""
        # Create child with small initial balance
        child = User(
            username="lowbalancechild",
            email="lowbalance@test.com",
            hashed_password="hashed",
            is_parent=False,
            is_active=True,
            parent_id=parent_user.id
        )
        db_session.add(child)
        await db_session.commit()
        
        # Add small initial balance
        initial = RewardAdjustment(
            parent_id=parent_user.id,
            child_id=child.id,
            amount=Decimal("10.00"),
            reason="Small initial balance"
        )
        db_session.add(initial)
        await db_session.commit()
        
        service = RewardAdjustmentService()
        
        async def try_deduct(amount: Decimal):
            """Try to deduct amount, return success/failure."""
            adjustment_data = RewardAdjustmentCreate(
                child_id=child.id,
                amount=-amount,
                reason=f"Concurrent deduction of ${amount}"
            )
            try:
                await service.create_adjustment(
                    db=db_session,
                    adjustment_data=adjustment_data,
                    current_user_id=parent_user.id
                )
                return True
            except HTTPException:
                return False
        
        # Try to make 5 concurrent deductions of $5 each
        # Only 2 should succeed with initial balance of $10
        tasks = [try_deduct(Decimal("5.00")) for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        successful = sum(1 for r in results if r)
        failed = sum(1 for r in results if not r)
        
        assert successful == 2
        assert failed == 3
        
        # Verify final balance is exactly 0
        repo = RewardAdjustmentRepository()
        final_balance = await repo.calculate_total_adjustments(
            db_session, 
            child_id=child.id
        )
        assert final_balance == Decimal("0.00")
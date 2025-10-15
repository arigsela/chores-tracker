"""Repository for ChoreAssignment model - data access layer."""
from typing import Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.chore_assignment import ChoreAssignment
from ..models.chore import Chore


class ChoreAssignmentRepository(BaseRepository[ChoreAssignment]):
    """Repository for managing chore assignments."""

    def __init__(self):
        super().__init__(ChoreAssignment)

    async def get_by_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        eager_load: bool = True
    ) -> List[ChoreAssignment]:
        """Get all assignments for a specific chore.

        Args:
            db: Database session
            chore_id: ID of the chore
            eager_load: Whether to eager load relationships (chore, assignee)

        Returns:
            List of ChoreAssignment objects
        """
        query = select(ChoreAssignment).where(ChoreAssignment.chore_id == chore_id)

        if eager_load:
            query = query.options(
                joinedload(ChoreAssignment.chore),
                joinedload(ChoreAssignment.assignee)
            )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_assignee(
        self,
        db: AsyncSession,
        *,
        assignee_id: int,
        eager_load: bool = True
    ) -> List[ChoreAssignment]:
        """Get all assignments for a specific child.

        Args:
            db: Database session
            assignee_id: ID of the child user
            eager_load: Whether to eager load relationships

        Returns:
            List of ChoreAssignment objects
        """
        query = select(ChoreAssignment).where(
            ChoreAssignment.assignee_id == assignee_id
        )

        if eager_load:
            query = query.options(
                joinedload(ChoreAssignment.chore),
                joinedload(ChoreAssignment.assignee)
            )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_available_for_child(
        self,
        db: AsyncSession,
        *,
        assignee_id: int
    ) -> List[ChoreAssignment]:
        """Get available assignments for a child (not completed and outside cooldown).

        An assignment is available if:
        - Not currently completed (pending approval doesn't count as available)
        - For recurring chores: cooldown period has passed since last approval

        Args:
            db: Database session
            assignee_id: ID of the child user

        Returns:
            List of available ChoreAssignment objects with chore eagerly loaded
        """
        now = datetime.utcnow()

        # Get all assignments for the child with chore loaded
        query = (
            select(ChoreAssignment)
            .join(Chore, ChoreAssignment.chore_id == Chore.id)
            .where(
                and_(
                    ChoreAssignment.assignee_id == assignee_id,
                    ChoreAssignment.is_completed == False,  # Not completed
                    Chore.is_disabled == False  # Chore not disabled
                )
            )
            .options(
                joinedload(ChoreAssignment.chore),
                joinedload(ChoreAssignment.assignee)
            )
        )

        result = await db.execute(query)
        assignments = result.scalars().all()

        # Filter out assignments still in cooldown
        available_assignments = []
        for assignment in assignments:
            # If chore is recurring and has been approved before, check cooldown
            if assignment.chore.is_recurring and assignment.approval_date:
                cooldown_end = assignment.approval_date + timedelta(
                    days=assignment.chore.cooldown_days
                )
                if now >= cooldown_end:
                    available_assignments.append(assignment)
            else:
                # Not recurring or never approved, so it's available
                available_assignments.append(assignment)

        return available_assignments

    async def get_pending_approval(
        self,
        db: AsyncSession,
        *,
        creator_id: Optional[int] = None,
        family_id: Optional[int] = None
    ) -> List[ChoreAssignment]:
        """Get assignments that are completed but not yet approved.

        Can filter by creator_id (single parent) or family_id (all parents in family).

        Args:
            db: Database session
            creator_id: Optional - filter by chore creator ID
            family_id: Optional - filter by family ID

        Returns:
            List of pending ChoreAssignment objects with relationships loaded
        """
        # Base query for pending approval
        query = (
            select(ChoreAssignment)
            .join(Chore, ChoreAssignment.chore_id == Chore.id)
            .where(
                and_(
                    ChoreAssignment.is_completed == True,
                    ChoreAssignment.is_approved == False
                )
            )
        )

        # Filter by creator if provided
        if creator_id is not None:
            query = query.where(Chore.creator_id == creator_id)

        # Filter by family if provided
        if family_id is not None:
            from ..models.user import User  # Import here to avoid circular import
            query = query.join(User, User.id == Chore.creator_id).where(
                User.family_id == family_id
            )

        # Eager load relationships
        query = query.options(
            joinedload(ChoreAssignment.chore),
            joinedload(ChoreAssignment.assignee)
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_chore_and_assignee(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        assignee_id: int
    ) -> Optional[ChoreAssignment]:
        """Get a specific assignment by chore and assignee.

        Due to unique constraint, there can only be one assignment per (chore, assignee) pair.

        Args:
            db: Database session
            chore_id: ID of the chore
            assignee_id: ID of the assignee

        Returns:
            ChoreAssignment object or None
        """
        query = (
            select(ChoreAssignment)
            .where(
                and_(
                    ChoreAssignment.chore_id == chore_id,
                    ChoreAssignment.assignee_id == assignee_id
                )
            )
            .options(
                joinedload(ChoreAssignment.chore),
                joinedload(ChoreAssignment.assignee)
            )
        )

        result = await db.execute(query)
        return result.scalars().first()

    async def mark_completed(
        self,
        db: AsyncSession,
        *,
        assignment_id: int
    ) -> Optional[ChoreAssignment]:
        """Mark an assignment as completed.

        Args:
            db: Database session
            assignment_id: ID of the assignment

        Returns:
            Updated ChoreAssignment object
        """
        now = datetime.utcnow()
        return await self.update(
            db,
            id=assignment_id,
            obj_in={
                "is_completed": True,
                "completion_date": now,
                "is_approved": False,  # Reset approval status for new completion
                # Keep approval_date for cooldown tracking in recurring chores
                "rejection_reason": None
            }
        )

    async def approve_assignment(
        self,
        db: AsyncSession,
        *,
        assignment_id: int,
        reward_value: Optional[float] = None
    ) -> Optional[ChoreAssignment]:
        """Approve a completed assignment.

        Args:
            db: Database session
            assignment_id: ID of the assignment
            reward_value: Optional reward value for range-based rewards

        Returns:
            Updated ChoreAssignment object
        """
        now = datetime.utcnow()
        update_data = {
            "is_approved": True,
            "approval_date": now,
            "rejection_reason": None  # Clear any previous rejection
        }

        # Add reward value if provided (for range rewards)
        if reward_value is not None:
            update_data["approval_reward"] = reward_value

        return await self.update(db, id=assignment_id, obj_in=update_data)

    async def reject_assignment(
        self,
        db: AsyncSession,
        *,
        assignment_id: int,
        rejection_reason: str
    ) -> Optional[ChoreAssignment]:
        """Reject a completed assignment.

        Args:
            db: Database session
            assignment_id: ID of the assignment
            rejection_reason: Reason for rejection

        Returns:
            Updated ChoreAssignment object
        """
        return await self.update(
            db,
            id=assignment_id,
            obj_in={
                "is_completed": False,  # Reset to not completed
                "completion_date": None,
                "rejection_reason": rejection_reason,
                "approval_reward": None  # Clear any reward
            }
        )

    async def reset_assignment(
        self,
        db: AsyncSession,
        *,
        assignment_id: int
    ) -> Optional[ChoreAssignment]:
        """Reset an assignment to initial state (for recurring chores after cooldown).

        Args:
            db: Database session
            assignment_id: ID of the assignment

        Returns:
            Updated ChoreAssignment object
        """
        return await self.update(
            db,
            id=assignment_id,
            obj_in={
                "is_completed": False,
                "completion_date": None,
                "is_approved": False,  # Clear approval to start fresh cycle
                # Keep approval_date and approval_reward for history/cooldown tracking
                "rejection_reason": None
            }
        )

    async def get_assignment_history(
        self,
        db: AsyncSession,
        *,
        assignee_id: int,
        limit: int = 50
    ) -> List[ChoreAssignment]:
        """Get assignment history for a child (approved assignments).

        Args:
            db: Database session
            assignee_id: ID of the child user
            limit: Maximum number of assignments to return

        Returns:
            List of approved ChoreAssignment objects, ordered by approval date
        """
        query = (
            select(ChoreAssignment)
            .where(
                and_(
                    ChoreAssignment.assignee_id == assignee_id,
                    ChoreAssignment.is_approved == True
                )
            )
            .order_by(ChoreAssignment.approval_date.desc())
            .limit(limit)
            .options(
                joinedload(ChoreAssignment.chore),
                joinedload(ChoreAssignment.assignee)
            )
        )

        result = await db.execute(query)
        return result.scalars().all()

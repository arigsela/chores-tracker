"""Repository for Chore model - data access layer for multi-assignment chores."""
from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.chore import Chore
from ..models.chore_assignment import ChoreAssignment


class ChoreRepository(BaseRepository[Chore]):
    """Repository for managing chores with multi-assignment support."""

    def __init__(self):
        super().__init__(Chore)

    async def get_by_creator(
        self,
        db: AsyncSession,
        *,
        creator_id: int,
        include_disabled: bool = False
    ) -> List[Chore]:
        """Get all chores created by a user.

        Args:
            db: Database session
            creator_id: ID of the parent who created the chores
            include_disabled: Whether to include disabled chores

        Returns:
            List of Chore objects with assignments eagerly loaded
        """
        query = select(Chore).where(Chore.creator_id == creator_id)

        if not include_disabled:
            query = query.where(Chore.is_disabled == False)

        query = query.options(selectinload(Chore.assignments))

        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_family(
        self,
        db: AsyncSession,
        *,
        family_id: int,
        include_disabled: bool = False
    ) -> List[Chore]:
        """Get all chores created by any parent in the same family.

        Args:
            db: Database session
            family_id: ID of the family
            include_disabled: Whether to include disabled chores

        Returns:
            List of Chore objects
        """
        from ..models.user import User  # Import here to avoid circular import

        query = (
            select(Chore)
            .join(User, User.id == Chore.creator_id)
            .where(User.family_id == family_id)
        )

        if not include_disabled:
            query = query.where(Chore.is_disabled == False)

        query = query.options(selectinload(Chore.assignments))

        result = await db.execute(query)
        return result.scalars().all()

    async def get_unassigned_pool(
        self,
        db: AsyncSession,
        *,
        family_id: Optional[int] = None
    ) -> List[Chore]:
        """Get all unassigned pool chores (assignment_mode='unassigned').

        These are chores that any child in the family can claim.

        Args:
            db: Database session
            family_id: Optional - filter by family

        Returns:
            List of unassigned pool Chore objects
        """
        query = (
            select(Chore)
            .where(
                and_(
                    Chore.assignment_mode == 'unassigned',
                    Chore.is_disabled == False
                )
            )
            .options(selectinload(Chore.assignments))
        )

        # Filter by family if provided
        if family_id is not None:
            from ..models.user import User
            query = query.join(User, User.id == Chore.creator_id).where(
                User.family_id == family_id
            )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_chores_for_child(
        self,
        db: AsyncSession,
        *,
        child_id: int
    ) -> List[Chore]:
        """Get all chores that have assignments for a specific child.

        Includes chores in 'single' and 'multi_independent' modes where
        the child has an assignment.

        Args:
            db: Database session
            child_id: ID of the child user

        Returns:
            List of Chore objects with assignments eagerly loaded
        """
        query = (
            select(Chore)
            .join(ChoreAssignment, ChoreAssignment.chore_id == Chore.id)
            .where(
                and_(
                    ChoreAssignment.assignee_id == child_id,
                    Chore.is_disabled == False
                )
            )
            .options(selectinload(Chore.assignments))
            .distinct()
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def disable_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int
    ) -> Optional[Chore]:
        """Disable a chore (soft delete).

        Args:
            db: Database session
            chore_id: ID of the chore to disable

        Returns:
            Updated Chore object
        """
        return await self.update(
            db,
            id=chore_id,
            obj_in={"is_disabled": True}
        )

    async def enable_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int
    ) -> Optional[Chore]:
        """Enable a previously disabled chore.

        Args:
            db: Database session
            chore_id: ID of the chore to enable

        Returns:
            Updated Chore object
        """
        return await self.update(
            db,
            id=chore_id,
            obj_in={"is_disabled": False}
        )

    async def get_with_assignments(
        self,
        db: AsyncSession,
        *,
        chore_id: int
    ) -> Optional[Chore]:
        """Get a chore with all assignments eagerly loaded.

        Args:
            db: Database session
            chore_id: ID of the chore

        Returns:
            Chore object with assignments loaded, or None
        """
        query = (
            select(Chore)
            .where(Chore.id == chore_id)
            .options(selectinload(Chore.assignments))
        )

        result = await db.execute(query)
        return result.scalars().first()

    # ====================================================================
    # DEPRECATED METHODS - Kept for backward compatibility during migration
    # These methods reference old single-assignment fields that no longer exist
    # They should not be used in new code and will be removed in a future version
    # ====================================================================

    async def get_by_assignee(
        self,
        db: AsyncSession,
        *,
        assignee_id: int
    ) -> List[Chore]:
        """DEPRECATED: Get chores for an assignee.

        Use ChoreAssignmentRepository.get_by_assignee() instead.
        This method is kept for backward compatibility only.

        Args:
            db: Database session
            assignee_id: ID of the child

        Returns:
            List of Chore objects that have assignments for this child
        """
        print(f"WARNING: get_by_assignee() is deprecated. Use ChoreAssignmentRepository instead.")
        return await self.get_chores_for_child(db, child_id=assignee_id)

    async def get_available_for_assignee(
        self,
        db: AsyncSession,
        *,
        assignee_id: int
    ) -> List[Chore]:
        """DEPRECATED: Get available chores for an assignee.

        Use ChoreAssignmentRepository.get_available_for_child() instead.
        This method is kept for backward compatibility only.

        Args:
            db: Database session
            assignee_id: ID of the child

        Returns:
            Empty list - functionality moved to ChoreAssignmentRepository
        """
        print(f"WARNING: get_available_for_assignee() is deprecated. Use ChoreAssignmentRepository.get_available_for_child() instead.")
        return []

    async def get_pending_approval(
        self,
        db: AsyncSession,
        *,
        creator_id: int
    ) -> List[Chore]:
        """DEPRECATED: Get pending approval chores.

        Use ChoreAssignmentRepository.get_pending_approval() instead.
        This method is kept for backward compatibility only.

        Args:
            db: Database session
            creator_id: ID of the parent

        Returns:
            Empty list - functionality moved to ChoreAssignmentRepository
        """
        print(f"WARNING: get_pending_approval() is deprecated. Use ChoreAssignmentRepository.get_pending_approval() instead.")
        return []

    async def get_pending_approval_by_family(
        self,
        db: AsyncSession,
        *,
        family_id: int
    ) -> List[Chore]:
        """DEPRECATED: Get pending approval chores for family.

        Use ChoreAssignmentRepository.get_pending_approval(family_id=...) instead.
        This method is kept for backward compatibility only.

        Args:
            db: Database session
            family_id: ID of the family

        Returns:
            Empty list - functionality moved to ChoreAssignmentRepository
        """
        print(f"WARNING: get_pending_approval_by_family() is deprecated. Use ChoreAssignmentRepository.get_pending_approval() instead.")
        return []

    async def get_pending_approval_for_child(
        self,
        db: AsyncSession,
        *,
        assignee_id: int
    ) -> List[Chore]:
        """DEPRECATED: Get pending chores for a child.

        Use ChoreAssignmentRepository.get_by_assignee() with filtering instead.
        This method is kept for backward compatibility only.

        Args:
            db: Database session
            assignee_id: ID of the child

        Returns:
            Empty list - functionality moved to ChoreAssignmentRepository
        """
        print(f"WARNING: get_pending_approval_for_child() is deprecated. Use ChoreAssignmentRepository instead.")
        return []

    async def get_completed_by_child(
        self,
        db: AsyncSession,
        *,
        child_id: int
    ) -> List[Chore]:
        """DEPRECATED: Get completed chores for a child.

        Use ChoreAssignmentRepository.get_assignment_history() instead.
        This method is kept for backward compatibility only.

        Args:
            db: Database session
            child_id: ID of the child

        Returns:
            Empty list - functionality moved to ChoreAssignmentRepository
        """
        print(f"WARNING: get_completed_by_child() is deprecated. Use ChoreAssignmentRepository.get_assignment_history() instead.")
        return []

    async def mark_completed(
        self,
        db: AsyncSession,
        *,
        chore_id: int
    ) -> Optional[Chore]:
        """DEPRECATED: Mark a chore as completed.

        Use ChoreAssignmentRepository.mark_completed() instead.
        This method is kept for backward compatibility only.

        Args:
            db: Database session
            chore_id: ID of the chore

        Returns:
            None - functionality moved to ChoreAssignmentRepository
        """
        print(f"WARNING: mark_completed() is deprecated. Use ChoreAssignmentRepository.mark_completed() instead.")
        return None

    async def approve_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        reward_value: Optional[float] = None
    ) -> Optional[Chore]:
        """DEPRECATED: Approve a chore.

        Use ChoreAssignmentRepository.approve_assignment() instead.
        This method is kept for backward compatibility only.

        Args:
            db: Database session
            chore_id: ID of the chore
            reward_value: Optional reward value

        Returns:
            None - functionality moved to ChoreAssignmentRepository
        """
        print(f"WARNING: approve_chore() is deprecated. Use ChoreAssignmentRepository.approve_assignment() instead.")
        return None

    async def reset_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int
    ) -> Optional[Chore]:
        """DEPRECATED: Reset a chore.

        Use ChoreAssignmentRepository.reset_assignment() instead.
        This method is kept for backward compatibility only.

        Args:
            db: Database session
            chore_id: ID of the chore

        Returns:
            None - functionality moved to ChoreAssignmentRepository
        """
        print(f"WARNING: reset_chore() is deprecated. Use ChoreAssignmentRepository.reset_assignment() instead.")
        return None

    async def reset_disabled_chores(self, db: AsyncSession) -> int:
        """DEPRECATED: Reset disabled chores.

        This method is no longer needed with the new assignment architecture.

        Args:
            db: Database session

        Returns:
            0 - no longer applicable
        """
        print(f"WARNING: reset_disabled_chores() is deprecated and no longer needed.")
        return 0

"""
Chore service with business logic for chore operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseService
from ..models.chore import Chore
from ..models.user import User
from ..repositories.chore import ChoreRepository
from ..repositories.chore_assignment import ChoreAssignmentRepository
from ..repositories.user import UserRepository
from ..repositories.reward_adjustment import RewardAdjustmentRepository
from ..core.unit_of_work import UnitOfWork
from .activity_service import ActivityService
from ..schemas.chore import ChoreResponse
from ..schemas.assignment import AssignmentResponse
from ..schemas.user import UserResponse
from ..schemas.reward_adjustment import RewardAdjustmentResponse


class ChoreService(BaseService[Chore, ChoreRepository]):
    """Service for chore-related business logic."""

    def __init__(self):
        """Initialize chore service."""
        super().__init__(ChoreRepository())
        self.user_repo = UserRepository()
        self.assignment_repo = ChoreAssignmentRepository()
        self.reward_repo = RewardAdjustmentRepository()
        self.activity_service = ActivityService()
    
    async def create_chore(
        self,
        db: AsyncSession,
        *,
        creator_id: int,
        chore_data: Dict[str, Any]
    ) -> Chore:
        """
        Create a new chore with multi-assignment support.

        Business rules:
        - Only parents can create chores
        - assignment_mode determines how chore is assigned:
          * 'single': Exactly 1 assignee_id required
          * 'multi_independent': 1+ assignee_ids required
          * 'unassigned': 0 assignee_ids (pool chore)
        - All assignees must be children in the same family as creator
        - Validate reward values for range rewards
        """
        # Get creator to validate family membership
        creator = await self.user_repo.get(db, id=creator_id)
        if not creator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator not found"
            )

        # Extract assignment data
        assignment_mode = chore_data.get("assignment_mode", "single")
        assignee_ids = chore_data.get("assignee_ids", [])

        # Validate assignment mode rules
        if assignment_mode == "single":
            if len(assignee_ids) != 1:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="'single' assignment mode requires exactly 1 assignee_id"
                )
        elif assignment_mode == "multi_independent":
            if len(assignee_ids) < 1:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="'multi_independent' assignment mode requires at least 1 assignee_id"
                )
        elif assignment_mode == "unassigned":
            if len(assignee_ids) != 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="'unassigned' assignment mode must have 0 assignee_ids"
                )

        # Validate all assignees exist and belong to creator's family
        assignees = []
        for assignee_id in assignee_ids:
            assignee = await self.user_repo.get(db, id=assignee_id)
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assignee with ID {assignee_id} not found"
                )

            # Family-based access control
            if creator.family_id and assignee.family_id:
                # Both users are in families - check if they're in the same family
                if creator.family_id != assignee.family_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Assignee {assignee_id} is not in your family. You can only assign chores to children in your family"
                    )
            else:
                # Legacy single-parent mode - use original validation
                if assignee.parent_id != creator_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Assignee {assignee_id} is not your child. You can only assign chores to your own children"
                    )

            assignees.append(assignee)

        # Validate range rewards
        if chore_data.get("is_range_reward"):
            min_reward = chore_data.get("min_reward", 0)
            max_reward = chore_data.get("max_reward", 0)
            if min_reward > max_reward:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Minimum reward must be less than maximum reward"
                )

        # Prepare chore data (remove assignment-specific fields)
        clean_chore_data = {k: v for k, v in chore_data.items() if k not in ["assignee_ids"]}
        clean_chore_data["creator_id"] = creator_id
        clean_chore_data["assignment_mode"] = assignment_mode

        # Create chore
        chore = await self.repository.create(db, obj_in=clean_chore_data)

        # Create ChoreAssignment records for each assignee
        created_assignments = []
        for assignee in assignees:
            assignment_data = {
                "chore_id": chore.id,
                "assignee_id": assignee.id,
                "is_completed": False,
                "is_approved": False
            }
            assignment = await self.assignment_repo.create(db, obj_in=assignment_data)
            created_assignments.append(assignment)

        # Log activity for each assignment
        try:
            reward_amount = None
            if not chore_data.get("is_range_reward"):
                reward_amount = chore_data.get("reward")

            for assignee in assignees:
                await self.activity_service.log_chore_created(
                    db,
                    parent_id=creator_id,
                    child_id=assignee.id,
                    chore_id=chore.id,
                    chore_title=chore.title,
                    reward_amount=reward_amount
                )
        except Exception as e:
            # Don't fail chore creation if activity logging fails
            print(f"Failed to log chore creation activity: {e}")

        return chore
    
    async def get_chores_for_user(
        self,
        db: AsyncSession,
        *,
        user: User
    ) -> List[Chore]:
        """
        Get chores based on user role with family-aware access control.
        
        - Parents see chores created by any parent in their family (or just their own if no family)
        - Children see chores assigned to them (excluding disabled)
        """
        if user.is_parent:
            # Family-aware logic for parents
            if user.family_id:
                return await self.repository.get_by_family(db, family_id=user.family_id)
            else:
                # Fallback for parents without families
                return await self.repository.get_by_creator(db, creator_id=user.id)
        else:
            return await self.repository.get_by_assignee(db, assignee_id=user.id)
    
    async def get_available_chores(
        self,
        db: AsyncSession,
        *,
        child_id: int
    ) -> Dict[str, Any]:
        """
        Get available chores for a child with multi-assignment support.

        Returns chores from two sources:
        1. **Assigned chores**: Child has assignment, not completed, outside cooldown
        2. **Pool chores**: Unassigned mode chores available to claim

        Returns:
            Dictionary with 'assigned' and 'pool' lists, each containing chore + assignment data
        """
        # Get child user
        child = await self.user_repo.get(db, id=child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )

        # Get all assignments for this child
        all_assignments = await self.assignment_repo.get_by_assignee(db, assignee_id=child_id)

        assigned_chores = []
        for assignment in all_assignments:
            # Skip completed assignments (pending approval or approved)
            if assignment.is_completed:
                continue

            # Get chore with assignments loaded
            chore = await self.repository.get_with_assignments(db, chore_id=assignment.chore_id)
            if not chore or chore.is_disabled:
                continue

            # Check cooldown for recurring chores
            if chore.is_recurring and assignment.is_approved and assignment.approval_date:
                cooldown_end = assignment.approval_date + timedelta(days=chore.cooldown_days)
                now = datetime.utcnow()
                if now < cooldown_end:
                    # Still in cooldown, skip
                    continue

            # This chore is available - convert to schemas for serialization
            assigned_chores.append({
                "chore": ChoreResponse.model_validate(chore),
                "assignment": AssignmentResponse.model_validate(assignment),
                "assignment_id": assignment.id
            })

        # Get unassigned pool chores
        pool_chores_raw = await self.repository.get_unassigned_pool(db)
        pool_chores = []

        for chore in pool_chores_raw:
            if chore.is_disabled:
                continue

            # Check if child already has an assignment for this chore
            existing_assignment = await self.assignment_repo.get_by_chore_and_assignee(
                db, chore_id=chore.id, assignee_id=child_id
            )

            if existing_assignment:
                # Child already claimed this, skip (it's in assigned_chores or completed)
                continue

            # Available to claim - convert to schema for serialization
            pool_chores.append({
                "chore": ChoreResponse.model_validate(chore),
                "assignment": None,  # No assignment yet
                "assignment_id": None
            })

        return {
            "assigned": assigned_chores,
            "pool": pool_chores,
            "total_count": len(assigned_chores) + len(pool_chores)
        }

    async def get_pending_approval(
        self,
        db: AsyncSession,
        *,
        parent_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get assignments pending approval for a parent with multi-assignment support.

        Returns assignment-level data (not chore-level) with assignee details.
        Family-aware: parent sees pending assignments from all family chores.

        Returns:
            List of dictionaries with assignment, chore, and assignee data
        """
        # Get parent user
        parent = await self.user_repo.get(db, id=parent_id)
        if not parent:
            return []

        # Get pending assignments based on family membership
        if parent.family_id:
            # Family mode: get all pending assignments from family chores
            pending_assignments = await self.assignment_repo.get_pending_approval(
                db, family_id=parent.family_id
            )
        else:
            # Legacy mode: get pending assignments from parent's chores only
            pending_assignments = await self.assignment_repo.get_pending_approval(
                db, creator_id=parent_id
            )

        # Build result with full context
        result = []
        for assignment in pending_assignments:
            # Get chore with assignments
            chore = await self.repository.get_with_assignments(db, chore_id=assignment.chore_id)
            if not chore:
                continue

            # Get assignee details
            assignee = await self.user_repo.get(db, id=assignment.assignee_id)
            if not assignee:
                continue

            # Convert models to schemas for serialization
            result.append({
                "assignment": AssignmentResponse.model_validate(assignment),
                "assignment_id": assignment.id,
                "chore": ChoreResponse.model_validate(chore),
                "assignee": UserResponse.model_validate(assignee),
                "assignee_name": assignee.username
            })

        return result
    
    async def get_child_chores(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        child_id: int
    ) -> List[Chore]:
        """
        Get all chores for a specific child (updated for multi-assignment architecture).

        Business rules:
        - Only parents can view children's chores
        - Child must belong to the parent

        Returns chores with assignment data populated for proper frontend filtering.
        """
        # Verify child belongs to parent
        child = await self.user_repo.get(db, id=child_id)
        if not child or child.parent_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found or not your child"
            )

        # Get assignments for the child (with eagerly loaded chore relationships)
        assignments = await self.assignment_repo.get_by_assignee(db, assignee_id=child_id)

        # Extract unique chores and populate assignment data on them
        from sqlalchemy.orm import make_transient
        chores = []
        for assignment in assignments:
            chore = assignment.chore
            # Populate assignment-level fields on the chore for backward compatibility
            # This allows frontend to filter by is_completed/is_approved without breaking
            chore.is_completed = assignment.is_completed
            chore.is_approved = assignment.is_approved
            chore.completed_at = assignment.completion_date
            chore.approved_at = assignment.approval_date
            chore.approval_reward = assignment.approval_reward
            chore.rejection_reason = assignment.rejection_reason

            # Detach from session to prevent lazy loading of relationships during serialization
            make_transient(chore)
            chores.append(chore)

        return chores
    
    async def complete_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Mark a chore assignment as complete with multi-assignment support.

        Business rules:
        - Chore must not be disabled
        - **Single/Multi-independent**: Child must have existing assignment, mark it completed
        - **Unassigned**: Create new assignment for child (claim), mark it completed
        - For recurring chores: Check cooldown based on assignment's approval_date

        Returns:
            Dictionary with chore and assignment information
        """
        # Get chore with assignments eagerly loaded
        chore = await self.repository.get_with_assignments(db, chore_id=chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )

        # Check if chore is disabled
        if chore.is_disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot complete a disabled chore"
            )

        # Get user to check family membership
        user = await self.user_repo.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        assignment = None

        # Handle based on assignment_mode
        if chore.assignment_mode == "single" or chore.assignment_mode == "multi_independent":
            # For single/multi_independent: child must have an existing assignment
            assignment = await self.assignment_repo.get_by_chore_and_assignee(
                db,
                chore_id=chore_id,
                assignee_id=user_id
            )

            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to this chore"
                )

            # Check if already completed (pending approval)
            if assignment.is_completed and not assignment.is_approved:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This chore is already completed and pending approval"
                )

            # Check cooldown for recurring chores
            if chore.is_recurring and assignment.is_approved and assignment.approval_date:
                cooldown_end = assignment.approval_date + timedelta(days=chore.cooldown_days)
                now = datetime.utcnow()
                if now < cooldown_end:
                    remaining_days = (cooldown_end - now).days + 1
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Chore is in cooldown period. Available again in {remaining_days} days"
                    )

                # Reset assignment for recurring chore (approved assignment can be redone)
                assignment = await self.assignment_repo.reset_assignment(
                    db,
                    assignment_id=assignment.id
                )

            # Mark assignment as completed
            assignment = await self.assignment_repo.mark_completed(
                db,
                assignment_id=assignment.id
            )

        elif chore.assignment_mode == "unassigned":
            # For unassigned pool chores: create assignment (claim) and mark completed
            # First check if child already has an assignment for this chore
            existing_assignment = await self.assignment_repo.get_by_chore_and_assignee(
                db,
                chore_id=chore_id,
                assignee_id=user_id
            )

            if existing_assignment:
                # Child already claimed this chore
                if existing_assignment.is_completed and not existing_assignment.is_approved:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="You have already completed this chore and it's pending approval"
                    )

                # Check cooldown
                if chore.is_recurring and existing_assignment.is_approved and existing_assignment.approval_date:
                    cooldown_end = existing_assignment.approval_date + timedelta(days=chore.cooldown_days)
                    now = datetime.utcnow()
                    if now < cooldown_end:
                        remaining_days = (cooldown_end - now).days + 1
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"You completed this chore recently. Available again in {remaining_days} days"
                        )

                    # Reset for recurring
                    assignment = await self.assignment_repo.reset_assignment(
                        db,
                        assignment_id=existing_assignment.id
                    )

                # Mark as completed
                assignment = await self.assignment_repo.mark_completed(
                    db,
                    assignment_id=existing_assignment.id
                )
            else:
                # Create new assignment (claim the chore)
                assignment_data = {
                    "chore_id": chore_id,
                    "assignee_id": user_id,
                    "is_completed": True,  # Claim and complete in one step
                    "is_approved": False,
                    "completion_date": datetime.utcnow()
                }
                assignment = await self.assignment_repo.create(db, obj_in=assignment_data)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown assignment mode: {chore.assignment_mode}"
            )

        # Log activity
        try:
            await self.activity_service.log_chore_completed(
                db,
                child_id=user_id,
                chore_id=chore_id,
                chore_title=chore.title
            )
        except Exception as e:
            # Don't fail chore completion if activity logging fails
            print(f"Failed to log chore completion activity: {e}")

        # Convert models to schemas for serialization
        return {
            "chore": ChoreResponse.model_validate(chore),
            "assignment": AssignmentResponse.model_validate(assignment),
            "message": "Chore completed successfully"
        }

    async def approve_assignment(
        self,
        db: AsyncSession,
        *,
        assignment_id: int,
        parent_id: int,
        reward_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Approve a completed assignment with multi-assignment support.

        Business rules:
        - Parent must be in same family as chore creator
        - Assignment must be completed but not approved
        - For range rewards, reward_value is required and must be within range
        - Creates RewardAdjustment to track child's balance increase
        - Updates activity log

        Returns:
            Dictionary with assignment and reward adjustment
        """
        # Get assignment with chore and assignee loaded
        assignment = await self.assignment_repo.get(db, id=assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )

        # Get chore with assignments
        chore = await self.repository.get_with_assignments(db, chore_id=assignment.chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )

        # Check if assignment is completed
        if not assignment.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment must be completed before approval"
            )

        # Check if already approved
        if assignment.is_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment is already approved"
            )

        # Get parent and verify authorization
        parent = await self.user_repo.get(db, id=parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent not found"
            )

        # Get chore creator to check family access
        creator = await self.user_repo.get(db, id=chore.creator_id)
        if not creator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore creator not found"
            )

        # Family-based access control: parent must be in same family as creator
        if parent.family_id and creator.family_id:
            if parent.family_id != creator.family_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only approve assignments from your family"
                )
        else:
            # Legacy single-parent mode: parent must be the creator
            if chore.creator_id != parent_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only approve assignments for chores you created"
                )

        # Determine final reward amount
        final_reward = chore.reward

        if chore.is_range_reward:
            # For range rewards, reward_value is required
            if reward_value is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Reward value is required for range-based rewards"
                )

            # Validate reward is within range
            if reward_value < chore.min_reward or reward_value > chore.max_reward:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Reward value must be between {chore.min_reward} and {chore.max_reward}"
                )

            final_reward = reward_value

        # Approve the assignment
        approved_assignment = await self.assignment_repo.approve_assignment(
            db,
            assignment_id=assignment_id,
            reward_value=final_reward if chore.is_range_reward else None
        )

        # Create RewardAdjustment to update child's balance
        reward_adjustment = await self.reward_repo.create(
            db,
            obj_in={
                "child_id": assignment.assignee_id,
                "parent_id": parent_id,
                "amount": final_reward,
                "reason": f"Approved chore: {chore.title}"
            }
        )

        # Log activity
        try:
            await self.activity_service.log_chore_approved(
                db,
                parent_id=parent_id,
                child_id=assignment.assignee_id,
                chore_id=chore.id,
                chore_title=chore.title,
                reward_amount=final_reward
            )
        except Exception as e:
            # Don't fail approval if activity logging fails
            print(f"Failed to log chore approval activity: {e}")

        # Convert models to schemas for serialization
        return {
            "assignment": AssignmentResponse.model_validate(approved_assignment),
            "reward_adjustment": RewardAdjustmentResponse.model_validate(reward_adjustment),
            "chore": ChoreResponse.model_validate(chore),
            "final_reward": final_reward,
            "message": "Assignment approved successfully"
        }

    async def reject_assignment(
        self,
        db: AsyncSession,
        *,
        assignment_id: int,
        parent_id: int,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """
        Reject a completed assignment with multi-assignment support.

        Business rules:
        - Parent must be in same family as chore creator
        - Assignment must be completed but not approved
        - Rejection reason is required and must not be empty
        - Resets assignment: is_completed=False, completion_date=None
        - Sets rejection_reason for child to see
        - Updates activity log

        Returns:
            Dictionary with rejected assignment and chore
        """
        # Get assignment
        assignment = await self.assignment_repo.get(db, id=assignment_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )

        # Get chore
        chore = await self.repository.get_with_assignments(db, chore_id=assignment.chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )

        # Check if assignment is completed
        if not assignment.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment must be completed before rejection"
            )

        # Check if already approved
        if assignment.is_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reject already approved assignment"
            )

        # Validate rejection reason
        if not rejection_reason or not rejection_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rejection reason is required and cannot be empty"
            )

        # Get parent and verify authorization
        parent = await self.user_repo.get(db, id=parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent not found"
            )

        # Get chore creator to check family access
        creator = await self.user_repo.get(db, id=chore.creator_id)
        if not creator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore creator not found"
            )

        # Family-based access control: parent must be in same family as creator
        if parent.family_id and creator.family_id:
            if parent.family_id != creator.family_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only reject assignments from your family"
                )
        else:
            # Legacy single-parent mode: parent must be the creator
            if chore.creator_id != parent_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only reject assignments for chores you created"
                )

        # Reject the assignment - reset completion status
        rejected_assignment = await self.assignment_repo.update(
            db,
            id=assignment_id,
            obj_in={
                "is_completed": False,
                "completion_date": None,
                "rejection_reason": rejection_reason.strip()
            }
        )

        # Log activity
        try:
            await self.activity_service.log_chore_rejected(
                db,
                parent_id=parent_id,
                child_id=assignment.assignee_id,
                chore_id=chore.id,
                chore_title=chore.title,
                rejection_reason=rejection_reason.strip()
            )
        except Exception as e:
            # Don't fail rejection if activity logging fails
            print(f"Failed to log chore rejection activity: {e}")

        # Convert models to schemas for serialization
        return {
            "assignment": AssignmentResponse.model_validate(rejected_assignment),
            "chore": ChoreResponse.model_validate(chore),
            "rejection_reason": rejection_reason.strip(),
            "message": "Assignment rejected successfully. Child can see the reason and redo the chore."
        }

    async def approve_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        parent_id: int,
        reward_value: Optional[float] = None
    ) -> Chore:
        """
        Approve a completed chore.
        
        Business rules:
        - Only parent who created the chore can approve
        - Chore must be completed
        - For range rewards, reward_value must be provided and within range
        """
        chore = await self.get(db, id=chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )
        
        # Check if user has permission to approve this chore (family-based access control)
        approver = await self.user_repo.get(db, id=parent_id)
        if not approver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approver not found"
            )
        
        creator = await self.user_repo.get(db, id=chore.creator_id)
        if not creator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore creator not found"
            )
        
        # Family-based access control: approver must be in same family as creator
        if approver.family_id and creator.family_id:
            # Both users are in families - check if they're in the same family
            if approver.family_id != creator.family_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only approve chores from your family"
                )
        else:
            # Legacy single-parent mode - use original validation
            if chore.creator_id != parent_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only approve chores you created"
                )
        
        # Check if chore is completed
        if not chore.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chore must be completed before approval"
            )
        
        # Check if already approved
        if chore.is_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chore is already approved"
            )
        
        # Validate reward for range rewards
        update_data = {"is_approved": True}
        
        if chore.is_range_reward:
            if reward_value is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Reward value is required for range-based rewards"
                )
            if reward_value < chore.min_reward or reward_value > chore.max_reward:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Reward value must be between {chore.min_reward} and {chore.max_reward}"
                )
            update_data["approval_reward"] = reward_value
            # Also update the reward field to the final approved amount
            update_data["reward"] = reward_value
        
        # Approve chore
        updated_chore = await self.repository.update(
            db, id=chore_id, obj_in=update_data
        )
        
        # Log activity
        try:
            final_reward = reward_value if reward_value is not None else chore.reward
            await self.activity_service.log_chore_approved(
                db,
                parent_id=parent_id,
                child_id=chore.assignee_id or chore.assigned_to_id,
                chore_id=chore_id,
                chore_title=updated_chore.title,
                reward_amount=final_reward or 0.0
            )
        except Exception as e:
            # Don't fail chore approval if activity logging fails
            print(f"Failed to log chore approval activity: {e}")
        
        return updated_chore
    
    async def reject_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        parent_id: int,
        rejection_reason: str
    ) -> Chore:
        """
        Reject a completed chore.
        
        Business rules:
        - Only parent who created the chore can reject
        - Chore must be completed but not approved
        - Rejection reason is required
        """
        chore = await self.get(db, id=chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )
        
        # Check if user is the creator
        if chore.creator_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only reject chores you created"
            )
        
        # Check if chore is completed
        if not chore.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chore must be completed before rejection"
            )
        
        # Check if already approved
        if chore.is_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reject already approved chore"
            )
        
        # Validate rejection reason
        if not rejection_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rejection reason is required"
            )
        
        # Reject chore - reset completion status and add rejection reason
        update_data = {
            "is_completed": False,
            "completion_date": None,
            "rejection_reason": rejection_reason.strip()
        }
        
        # Reject chore
        updated_chore = await self.repository.update(
            db, id=chore_id, obj_in=update_data
        )
        
        # Log activity
        try:
            await self.activity_service.log_chore_rejected(
                db,
                parent_id=parent_id,
                child_id=chore.assignee_id or chore.assigned_to_id,
                chore_id=chore_id,
                chore_title=updated_chore.title,
                rejection_reason=rejection_reason
            )
        except Exception as e:
            # Don't fail chore rejection if activity logging fails
            print(f"Failed to log chore rejection activity: {e}")
        
        return updated_chore
    
    async def update_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        parent_id: int,
        update_data: Dict[str, Any]
    ) -> Chore:
        """
        Update a chore.

        Business rules:
        - Only parent who created the chore can update
        - Cannot update if any assignments are completed/approved
        """
        chore = await self.repository.get_with_assignments(db, chore_id=chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )

        # Check if user is the creator
        if chore.creator_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update chores you created"
            )

        # Check if any assignments are already completed or approved
        if chore.assignments:
            for assignment in chore.assignments:
                if assignment.is_completed or assignment.is_approved:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot update chore with completed or approved assignments"
                    )

        # Update chore
        return await self.repository.update(
            db, id=chore_id, obj_in=update_data
        )
    
    async def disable_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        parent_id: int
    ) -> Chore:
        """
        Disable a chore (soft delete).
        
        Business rules:
        - Only parent who created the chore can disable
        """
        chore = await self.get(db, id=chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )
        
        # Check if user is the creator
        if chore.creator_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only disable chores you created"
            )
        
        # Disable chore
        return await self.repository.update(
            db, id=chore_id, obj_in={"is_disabled": True}
        )
    
    async def delete_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        parent_id: int
    ) -> None:
        """
        Delete a chore (hard delete).
        
        Business rules:
        - Only parent who created the chore can delete
        """
        chore = await self.get(db, id=chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )
        
        # Check if user is the creator
        if chore.creator_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete chores you created"
            )
        
        # Delete chore
        await self.repository.delete(db, id=chore_id)
    
    async def bulk_assign_chores(
        self,
        uow: UnitOfWork,
        *,
        creator_id: int,
        assignments: List[Dict[str, Any]]
    ) -> List[Chore]:
        """
        Bulk assign multiple chores to children in a single transaction.
        
        This ensures all assignments succeed or none do.
        
        Args:
            uow: Unit of Work for transaction management
            creator_id: ID of the parent creating the chores
            assignments: List of chore assignments, each containing:
                - title: Chore title
                - description: Chore description
                - assignee_id: ID of child to assign to
                - reward: Reward amount
                - Other chore fields...
                
        Returns:
            List of created chores
            
        Example:
            async with UnitOfWork() as uow:
                chores = await chore_service.bulk_assign_chores(
                    uow,
                    creator_id=parent_id,
                    assignments=[
                        {"title": "Clean room", "assignee_id": child1_id, "reward": 5.0},
                        {"title": "Do homework", "assignee_id": child2_id, "reward": 10.0}
                    ]
                )
                await uow.commit()
        """
        created_chores = []
        
        try:
            for assignment in assignments:
                # Validate assignee
                assignee_id = assignment.get("assignee_id")
                if assignee_id:
                    assignee = await uow.users.get(uow.session, id=assignee_id)
                    if not assignee:
                        raise ValueError(f"Assignee with ID {assignee_id} not found")
                    
                    if assignee.parent_id != creator_id:
                        raise ValueError(f"Child with ID {assignee_id} does not belong to this parent")
                
                # Create chore data
                chore_data = {
                    "title": assignment["title"],
                    "description": assignment.get("description", ""),
                    "reward": assignment["reward"],
                    "is_range_reward": assignment.get("is_range_reward", False),
                    "min_reward": assignment.get("min_reward"),
                    "max_reward": assignment.get("max_reward"),
                    "cooldown_days": assignment.get("cooldown_days", 0),
                    "is_recurring": assignment.get("is_recurring", False),
                    "creator_id": creator_id,
                    "assignee_id": assignee_id,
                    "is_completed": False,
                    "is_approved": False,
                    "is_disabled": False
                }
                
                # Create chore
                chore = await uow.chores.create(uow.session, obj_in=chore_data)
                created_chores.append(chore)
            
            return created_chores
            
        except Exception as e:
            # Transaction will be rolled back automatically by UnitOfWork
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to bulk assign chores: {str(e)}"
            )
    
    async def approve_chore_with_next_instance(
        self,
        uow: UnitOfWork,
        *,
        chore_id: int,
        parent_id: int,
        reward_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Approve a chore and create the next instance if it's recurring.
        
        This is a transactional operation ensuring both approval and next instance
        creation succeed together.
        
        Args:
            uow: Unit of Work for transaction management
            chore_id: ID of chore to approve
            parent_id: ID of parent approving the chore
            reward_value: Actual reward amount (for range rewards)
            
        Returns:
            Dictionary with approved chore and next instance (if created)
        """
        try:
            # Get the chore
            chore = await uow.chores.get(uow.session, id=chore_id)
            if not chore:
                raise ValueError("Chore not found")
            
            # Validate parent is the creator
            if chore.creator_id != parent_id:
                raise ValueError("You can only approve chores you created")
            
            # Validate chore is completed but not approved
            if not chore.is_completed:
                raise ValueError("Chore must be completed before approval")
            if chore.is_approved:
                raise ValueError("Chore is already approved")
            
            # Prepare approval data
            update_data = {
                "is_approved": True,
                "completion_date": datetime.now()
            }
            
            # Handle range rewards
            if chore.is_range_reward:
                if reward_value is None:
                    raise ValueError("Reward value is required for range-based rewards")
                if reward_value < chore.min_reward or reward_value > chore.max_reward:
                    raise ValueError(f"Reward must be between {chore.min_reward} and {chore.max_reward}")
                update_data["approval_reward"] = reward_value
                # Also update the reward field to the final approved amount
                update_data["reward"] = reward_value
            
            # Approve the chore
            approved_chore = await uow.chores.update(
                uow.session, id=chore_id, obj_in=update_data
            )
            
            next_chore = None
            
            # Create next instance if recurring
            if chore.is_recurring and chore.cooldown_days > 0:
                # Calculate next available date
                next_available = datetime.now() + timedelta(days=chore.cooldown_days)
                
                # Create next instance
                next_chore_data = {
                    "title": chore.title,
                    "description": chore.description,
                    "reward": chore.reward if not chore.is_range_reward else None,
                    "is_range_reward": chore.is_range_reward,
                    "min_reward": chore.min_reward,
                    "max_reward": chore.max_reward,
                    "cooldown_days": chore.cooldown_days,
                    "is_recurring": True,
                    "frequency": chore.frequency,
                    "creator_id": chore.creator_id,
                    "assignee_id": chore.assignee_id,
                    "is_completed": False,
                    "is_approved": False,
                    "is_disabled": False,
                    "created_at": next_available  # Set creation date to future
                }
                
                next_chore = await uow.chores.create(uow.session, obj_in=next_chore_data)
            
            return {
                "approved_chore": approved_chore,
                "next_instance": next_chore
            }
            
        except Exception as e:
            # Transaction will be rolled back automatically by UnitOfWork
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to approve chore: {str(e)}"
            )
"""Assignment-specific API endpoints for multi-assignment support."""
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from ....db.base import get_db
from ....schemas.assignment import AssignmentApprove, AssignmentReject, AssignmentResponse
from ....dependencies.auth import get_current_user
from ....dependencies.services import ChoreServiceDep
from ....models.user import User

router = APIRouter()


@router.post(
    "/{assignment_id}/approve",
    response_model=Dict[str, Any],
    summary="Approve a completed assignment",
    description="""
    Approve a specific assignment that has been completed by a child.

    **Access**: Parents only

    **Multi-assignment context**:
    - Works with specific assignment IDs, not chore IDs
    - Essential for multi_independent mode where one chore has multiple assignments
    - Each child's work is approved independently

    **Reward handling**:
    - **Fixed rewards**: Automatically uses the preset reward amount
    - **Range rewards**: Parent must specify reward_value within min/max range

    **Workflow**:
    1. Child completes assignment
    2. Parent reviews and approves with final reward
    3. Child's balance is updated
    4. For recurring chores: cooldown period begins for this assignment

    **Returns**:
    - `assignment`: Updated assignment object
    - `chore`: The chore object
    - `message`: Success message
    """,
    responses={
        200: {
            "description": "Assignment approved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "assignment": {
                            "id": 15,
                            "chore_id": 3,
                            "assignee_id": 2,
                            "is_completed": True,
                            "is_approved": True,
                            "approval_date": "2024-12-24T17:00:00",
                            "approval_reward": 5.0
                        },
                        "chore": {
                            "id": 3,
                            "title": "Wash dishes",
                            "assignment_mode": "single"
                        },
                        "message": "Assignment approved successfully. Reward added to child's balance."
                    }
                }
            }
        },
        400: {
            "description": "Invalid reward value or assignment not completed",
            "content": {
                "application/json": {
                    "example": {"detail": "Reward value must be between 3.0 and 7.0"}
                }
            }
        },
        403: {
            "description": "Only parents can approve assignments"
        },
        404: {
            "description": "Assignment not found"
        }
    }
)
async def approve_assignment(
    assignment_id: int = Path(..., description="The ID of the assignment to approve"),
    approval_data: AssignmentApprove = Body(
        default=AssignmentApprove(),
        description="Approval data with optional reward value for range-based rewards"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Approve a completed assignment and set the final reward amount.

    For range-based rewards, the reward_value must be within the defined range.
    """
    # Only parents can approve assignments
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can approve assignments"
        )

    # Use service to approve assignment
    result = await chore_service.approve_assignment(
        db,
        assignment_id=assignment_id,
        parent_id=current_user.id,
        reward_value=approval_data.reward_value
    )
    return result


@router.post(
    "/{assignment_id}/reject",
    response_model=Dict[str, Any],
    summary="Reject a completed assignment",
    description="""
    Reject a specific assignment that has been completed by a child.

    **Access**: Parents only

    **Multi-assignment context**:
    - Works with specific assignment IDs, not chore IDs
    - Essential for multi_independent mode where each child's work is evaluated separately
    - One child's rejection doesn't affect other children's assignments

    **Workflow**:
    1. Child completes assignment
    2. Parent reviews and rejects with reason
    3. Assignment status reverts to incomplete
    4. Child can see rejection reason and redo the work

    **Rejection behavior**:
    - Assignment is_completed becomes False
    - completion_date is reset to None
    - rejection_reason is stored for child to view
    - Child can complete the assignment again

    **Returns**:
    - `assignment`: Updated assignment object with rejection reason
    - `chore`: The chore object
    - `message`: Success message
    """,
    responses={
        200: {
            "description": "Assignment rejected successfully",
            "content": {
                "application/json": {
                    "example": {
                        "assignment": {
                            "id": 15,
                            "chore_id": 3,
                            "assignee_id": 2,
                            "is_completed": False,
                            "is_approved": False,
                            "completion_date": None,
                            "rejection_reason": "Please clean more thoroughly and organize items properly"
                        },
                        "chore": {
                            "id": 3,
                            "title": "Clean Room",
                            "assignment_mode": "single"
                        },
                        "message": "Assignment rejected. Child can redo the work."
                    }
                }
            }
        },
        400: {
            "description": "Assignment not completed or already approved",
            "content": {
                "application/json": {
                    "example": {"detail": "Assignment must be completed before rejection"}
                }
            }
        },
        403: {
            "description": "Only parents can reject assignments"
        },
        404: {
            "description": "Assignment not found"
        },
        422: {
            "description": "Rejection reason is required"
        }
    }
)
async def reject_assignment(
    assignment_id: int = Path(..., description="The ID of the assignment to reject"),
    rejection_data: AssignmentReject = Body(..., description="Rejection data with reason"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Reject a completed assignment with a reason.

    The assignment will be reset to incomplete status and the child can redo it.
    """
    # Only parents can reject assignments
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can reject assignments"
        )

    # Use service to reject assignment
    result = await chore_service.reject_assignment(
        db,
        assignment_id=assignment_id,
        parent_id=current_user.id,
        rejection_reason=rejection_data.rejection_reason
    )
    return result

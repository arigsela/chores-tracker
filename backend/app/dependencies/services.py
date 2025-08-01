"""
Service dependencies for FastAPI dependency injection.
"""
from typing import Annotated
from fastapi import Depends

from ..services import UserService, ChoreService, RewardAdjustmentService


def get_user_service() -> UserService:
    """Get user service instance."""
    return UserService()


def get_chore_service() -> ChoreService:
    """Get chore service instance."""
    return ChoreService()


def get_reward_adjustment_service() -> RewardAdjustmentService:
    """Get reward adjustment service instance."""
    return RewardAdjustmentService()


# Type aliases for cleaner dependency injection
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ChoreServiceDep = Annotated[ChoreService, Depends(get_chore_service)]
RewardAdjustmentServiceDep = Annotated[RewardAdjustmentService, Depends(get_reward_adjustment_service)]
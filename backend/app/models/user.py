from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base_class import Base

if TYPE_CHECKING:
    from .chore import Chore
    from .chore_assignment import ChoreAssignment
    from .reward_adjustment import RewardAdjustment
    from .activity import Activity
    from .family import Family

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)  # Keep during migration
    family_id: Mapped[Optional[int]] = mapped_column(ForeignKey("families.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    # Chores
    chores_created: Mapped[List["Chore"]] = relationship(
        "Chore",
        back_populates="creator",
        foreign_keys="Chore.creator_id"
    )
    chore_assignments: Mapped[List["ChoreAssignment"]] = relationship(
        "ChoreAssignment",
        back_populates="assignee",
        foreign_keys="ChoreAssignment.assignee_id",
        cascade="all, delete-orphan"
    )

    # Family hierarchy
    children: Mapped[List["User"]] = relationship(
        "User",
        back_populates="parent",
        foreign_keys="User.parent_id"
    )
    parent: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="children",
        remote_side=id
    )

    # Reward adjustments
    adjustments_received: Mapped[List["RewardAdjustment"]] = relationship(
        "RewardAdjustment",
        back_populates="child",
        foreign_keys="RewardAdjustment.child_id"
    )
    adjustments_created: Mapped[List["RewardAdjustment"]] = relationship(
        "RewardAdjustment",
        back_populates="parent",
        foreign_keys="RewardAdjustment.parent_id"
    )

    # Activities
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="user",
        foreign_keys="Activity.user_id"
    )

    # Family
    family: Mapped[Optional["Family"]] = relationship(
        "Family",
        back_populates="members",
        foreign_keys="User.family_id"
    )

from typing import Optional, TYPE_CHECKING, List
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..db.base_class import Base

if TYPE_CHECKING:
    from .user import User
    from .chore_assignment import ChoreAssignment

class Chore(Base):
    __tablename__ = "chores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)

    # Reward settings
    reward: Mapped[float] = mapped_column(Float, default=0.0)
    min_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_range_reward: Mapped[bool] = mapped_column(Boolean, default=False)

    # Recurrence settings
    cooldown_days: Mapped[int] = mapped_column(default=0)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Deprecated, use cooldown_days

    # Assignment mode (NEW)
    assignment_mode: Mapped[str] = mapped_column(
        String(20),
        default='single',
        index=True
    )  # Values: 'single', 'multi_independent', 'unassigned'

    # Status
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="chores_created",
        foreign_keys=[creator_id]
    )
    assignments: Mapped[List["ChoreAssignment"]] = relationship(
        "ChoreAssignment",
        back_populates="chore",
        cascade="all, delete-orphan",
        foreign_keys="[ChoreAssignment.chore_id]"
    )

    # Properties
    @property
    def is_new(self) -> bool:
        """Check if the chore is newly created (within the last hour)."""
        if not self.created_at:
            return False

        from datetime import timedelta
        return datetime.utcnow() - self.created_at < timedelta(hours=1)

    @property
    def is_single_assignment(self) -> bool:
        """Check if chore uses single assignment mode."""
        return self.assignment_mode == 'single'

    @property
    def is_multi_independent(self) -> bool:
        """Check if chore uses multi-independent assignment mode."""
        return self.assignment_mode == 'multi_independent'

    @property
    def is_unassigned_pool(self) -> bool:
        """Check if chore is an unassigned pool chore."""
        return self.assignment_mode == 'unassigned'

    @property
    def has_assignments(self) -> bool:
        """Check if chore has any assignments."""
        return len(self.assignments) > 0

    @property
    def pending_approval_count(self) -> int:
        """Get count of assignments pending approval."""
        return sum(1 for assignment in self.assignments if assignment.is_pending_approval)

    @property
    def approved_count(self) -> int:
        """Get count of approved assignments."""
        return sum(1 for assignment in self.assignments if assignment.is_approved)

    def __repr__(self) -> str:
        """String representation for debugging."""
        # Avoid lazy-load of assignments after session closed
        return (
            f"<Chore(id={self.id}, title='{self.title}', "
            f"assignment_mode='{self.assignment_mode}')>"
        )

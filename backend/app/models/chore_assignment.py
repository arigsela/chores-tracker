"""ChoreAssignment model for tracking individual chore assignments to users."""
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy import Integer, Boolean, DateTime, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..db.base_class import Base

if TYPE_CHECKING:
    from .chore import Chore
    from .user import User


class ChoreAssignment(Base):
    """
    Represents an assignment of a chore to a specific user.

    This model enables many-to-many relationships between chores and users,
    allowing for flexible assignment patterns:
    - Single assignment (one child assigned to one chore)
    - Multi-independent (multiple children, each completes separately)
    - Unassigned pool (created dynamically when a child claims a chore)

    Each assignment tracks its own completion status, approval state, and reward.
    """
    __tablename__ = "chore_assignments"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign keys
    chore_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chores.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    assignee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Completion tracking
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Reward tracking
    approval_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    chore: Mapped["Chore"] = relationship(
        "Chore",
        back_populates="assignments",
        foreign_keys=[chore_id]
    )
    assignee: Mapped["User"] = relationship(
        "User",
        back_populates="chore_assignments",
        foreign_keys=[assignee_id]
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('chore_id', 'assignee_id', name='unique_chore_assignee'),
    )

    # Properties
    @property
    def is_pending_approval(self) -> bool:
        """Check if assignment is completed but not yet approved."""
        return self.is_completed and not self.is_approved

    @property
    def is_available(self) -> bool:
        """
        Check if assignment is available for completion.

        An assignment is available if:
        - Not currently completed (pending approval)
        - For recurring chores, cooldown period has passed
        """
        if self.is_completed:
            return False

        # For recurring chores, check if cooldown has passed
        if self.chore and self.chore.is_recurring and self.approval_date:
            from datetime import timedelta
            cooldown_end = self.approval_date + timedelta(days=self.chore.cooldown_days)
            return datetime.utcnow() >= cooldown_end

        return True

    @property
    def days_until_available(self) -> Optional[int]:
        """
        Calculate days remaining until assignment becomes available again.

        Returns None if:
        - Assignment is already available
        - Chore is not recurring
        - Assignment has never been approved
        """
        if not self.chore or not self.chore.is_recurring or not self.approval_date:
            return None

        if self.is_available:
            return 0

        from datetime import timedelta
        cooldown_end = self.approval_date + timedelta(days=self.chore.cooldown_days)
        remaining = cooldown_end - datetime.utcnow()
        return max(0, remaining.days)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<ChoreAssignment(id={self.id}, chore_id={self.chore_id}, "
            f"assignee_id={self.assignee_id}, completed={self.is_completed}, "
            f"approved={self.is_approved})>"
        )

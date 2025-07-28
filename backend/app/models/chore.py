from typing import Optional, TYPE_CHECKING, List
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..db.base import Base

if TYPE_CHECKING:
    from .user import User
    from .chore_visibility import ChoreVisibility


class RecurrenceType(str, Enum):
    """Chore recurrence type options."""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Chore(Base):
    __tablename__ = "chores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    reward: Mapped[float] = mapped_column(Float, default=0.0)
    min_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_range_reward: Mapped[bool] = mapped_column(Boolean, default=False)
    cooldown_days: Mapped[int] = mapped_column(default=0)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # New recurrence fields
    recurrence_type: Mapped[RecurrenceType] = mapped_column(SQLEnum(RecurrenceType), default=RecurrenceType.NONE)
    recurrence_value: Mapped[Optional[int]] = mapped_column(nullable=True)
    last_completion_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_available_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    assignee: Mapped[Optional["User"]] = relationship(back_populates="chores_assigned", foreign_keys=[assignee_id])
    creator: Mapped["User"] = relationship(back_populates="chores_created", foreign_keys=[creator_id])
    visibility_settings: Mapped[List["ChoreVisibility"]] = relationship(back_populates="chore", cascade="all, delete-orphan")

    @property
    def is_new(self) -> bool:
        """Check if the chore is newly created (within the last hour)."""
        if not self.created_at:
            return False
        
        from datetime import datetime, timedelta
        return datetime.utcnow() - self.created_at < timedelta(hours=1)

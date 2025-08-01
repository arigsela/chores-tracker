from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base

if TYPE_CHECKING:
    from .chore import Chore
    from .reward_adjustment import RewardAdjustment

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_parent: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    chores_assigned: Mapped[List["Chore"]] = relationship(back_populates="assignee", foreign_keys="Chore.assignee_id")
    chores_created: Mapped[List["Chore"]] = relationship(back_populates="creator", foreign_keys="Chore.creator_id")
    children: Mapped[List["User"]] = relationship("User", back_populates="parent", foreign_keys="User.parent_id")
    parent: Mapped[Optional["User"]] = relationship("User", back_populates="children", remote_side=id)
    
    # Reward adjustments
    adjustments_received: Mapped[List["RewardAdjustment"]] = relationship(back_populates="child", foreign_keys="RewardAdjustment.child_id")
    adjustments_created: Mapped[List["RewardAdjustment"]] = relationship(back_populates="parent", foreign_keys="RewardAdjustment.parent_id")

"""ChoreVisibility model for managing which users can see which chores."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

if TYPE_CHECKING:
    from .chore import Chore
    from .user import User


class ChoreVisibility(Base):
    """Model for tracking chore visibility settings per user."""
    
    __tablename__ = "chore_visibility"
    __table_args__ = (
        UniqueConstraint("chore_id", "user_id", name="unique_chore_user"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    chore_id: Mapped[int] = mapped_column(ForeignKey("chores.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chore: Mapped["Chore"] = relationship(back_populates="visibility_settings")
    user: Mapped["User"] = relationship(back_populates="hidden_chores")
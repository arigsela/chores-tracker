"""
Activity model for tracking user actions and events.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base


class Activity(Base):
    """Model representing user activity/actions in the system."""
    
    __tablename__ = "activities"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign key to user who performed the activity
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Type of activity (chore_completed, chore_approved, chore_rejected, etc.)
    activity_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        index=True
    )
    
    # Human-readable description of the activity
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Optional target user (e.g., child for whom chore was approved)
    target_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Flexible data storage for activity-specific information
    activity_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True,
        comment="Activity-specific data like chore_id, amount, etc."
    )
    
    # Timestamp when activity occurred
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="activities",
        foreign_keys=[user_id]
    )
    
    target_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[target_user_id],
        post_update=True  # Avoid circular references
    )
    
    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, type={self.activity_type}, user_id={self.user_id})>"
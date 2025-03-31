from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.base import Base

class Chore(Base):
    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text)
    reward = Column(Float, default=0.0)
    min_reward = Column(Float, nullable=True)
    max_reward = Column(Float, nullable=True)
    is_range_reward = Column(Boolean, default=False)
    cooldown_days = Column(Integer, default=0)
    is_recurring = Column(Boolean, default=False)
    frequency = Column(String(50), nullable=True)  # Added length for frequency
    is_completed = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    completion_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    assignee = relationship("User", back_populates="chores_assigned", foreign_keys=[assignee_id])
    creator = relationship("User", back_populates="chores_created", foreign_keys=[creator_id])

    @property
    def is_new(self) -> bool:
        """Check if the chore is newly created (within the last hour)."""
        if not self.created_at:
            return False
        
        from datetime import datetime, timedelta
        return datetime.utcnow() - self.created_at < timedelta(hours=1)

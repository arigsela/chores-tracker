from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.base import Base

class Chore(Base):
    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    reward = Column(Float, default=0.0)
    is_recurring = Column(Boolean, default=False)
    frequency = Column(String, nullable=True)  # daily, weekly, etc.
    is_completed = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    assignee_id = Column(Integer, ForeignKey("users.id"))
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    assignee = relationship("User", back_populates="chores_assigned", foreign_keys=[assignee_id])
    creator = relationship("User", back_populates="chores_created", foreign_keys=[creator_id])
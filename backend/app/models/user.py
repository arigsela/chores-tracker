from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_parent = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    chores_assigned = relationship("Chore", back_populates="assignee", foreign_keys="Chore.assignee_id")
    chores_created = relationship("Chore", back_populates="creator", foreign_keys="Chore.creator_id")
    children = relationship("User", backref="parent", remote_side=[id])

from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base

if TYPE_CHECKING:
    from .chore import Chore
    from .payment import Payment

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
    payments_received: Mapped[List["Payment"]] = relationship("Payment", back_populates="child", foreign_keys="Payment.child_id")
    payments_made: Mapped[List["Payment"]] = relationship("Payment", back_populates="parent", foreign_keys="Payment.parent_id")

from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, ForeignKey, DateTime, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..db.base_class import Base

if TYPE_CHECKING:
    from .user import User

class RewardAdjustment(Base):
    __tablename__ = "reward_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    child: Mapped["User"] = relationship("User", foreign_keys=[child_id], back_populates="adjustments_received")
    parent: Mapped["User"] = relationship("User", foreign_keys=[parent_id], back_populates="adjustments_created")
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db.base_class import Base

if TYPE_CHECKING:
    from .user import User


class Payment(Base):
    """
    Payment model for tracking payments and manual adjustments to children's reward balances.
    
    This model handles both regular payments (reducing balance) and manual adjustments
    (which can increase or decrease balance).
    """
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    is_adjustment: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    child_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    parent_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    child: Mapped["User"] = relationship("User", foreign_keys=[child_id], back_populates="payments_received")
    parent: Mapped["User"] = relationship("User", foreign_keys=[parent_id], back_populates="payments_made")
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base_class import Base

if TYPE_CHECKING:
    from .user import User

class Family(Base):
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invite_code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    invite_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    members: Mapped[List["User"]] = relationship(back_populates="family", foreign_keys="User.family_id")
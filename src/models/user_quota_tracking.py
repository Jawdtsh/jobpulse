import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import UUIDPrimaryKeyMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class UserQuotaTracking(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "user_quota_tracking"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    daily_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    purchased_extra: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tier_at_generation: Mapped[str | None] = mapped_column(String(20), nullable=True)

    user: Mapped["User"] = relationship("User")

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_quota_date"),)

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class UserPreferences(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint(
            "similarity_threshold BETWEEN 0.60 AND 1.00",
            name="ck_user_preferences_similarity_threshold",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    similarity_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    notification_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    user: Mapped["User"] = relationship("User")

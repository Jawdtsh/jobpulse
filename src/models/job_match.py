import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import UUIDPrimaryKeyMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.job import Job


class JobMatch(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("job_id", "user_id", name="uq_job_match"),)

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_clicked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    clicked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["Job"] = relationship("Job", back_populates="matches")
    user: Mapped["User"] = relationship("User", back_populates="job_matches")

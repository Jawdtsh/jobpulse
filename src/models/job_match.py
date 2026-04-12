import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.job import Job
    from src.models.user_cv import UserCV


class JobMatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_matches"
    __table_args__ = (
        UniqueConstraint("job_id", "user_id", "cv_id", name="uq_job_match_cv"),
    )

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
    cv_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_cvs.id", ondelete="CASCADE"),
        nullable=False,
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(nullable=True)
    is_clicked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    clicked_at: Mapped[datetime | None] = mapped_column(nullable=True)

    job: Mapped["Job"] = relationship("Job", back_populates="matches")
    user: Mapped["User"] = relationship("User", back_populates="job_matches")
    cv: Mapped["UserCV"] = relationship("UserCV")

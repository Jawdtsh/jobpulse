import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import UUIDPrimaryKeyMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.job import Job
    from src.models.user_cv import UserCV


class CoverLetterLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "cover_letter_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    cv_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_cvs.id", ondelete="CASCADE"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tone: Mapped[str] = mapped_column(
        String(20), nullable=False, default="professional"
    )
    length: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    focus_area: Mapped[str] = mapped_column(String(20), nullable=False, default="all")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="english")
    ai_model: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    generation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    counted_in_quota: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    user: Mapped["User"] = relationship("User", back_populates="cover_letter_logs")
    job: Mapped["Job | None"] = relationship("Job", back_populates="cover_letter_logs")
    cv: Mapped["UserCV | None"] = relationship("UserCV")

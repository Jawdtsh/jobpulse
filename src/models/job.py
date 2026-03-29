import uuid
from typing import TYPE_CHECKING, Any
from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector
from src.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.monitored_channel import MonitoredChannel
    from src.models.job_match import JobMatch
    from src.models.job_report import JobReport
    from src.models.cover_letter_log import CoverLetterLog


class Job(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "jobs"

    source_channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitored_channels.id", ondelete="SET NULL"),
        nullable=True,
    )
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    embedding_vector: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    source_channel: Mapped["MonitoredChannel | None"] = relationship(
        "MonitoredChannel",
        back_populates="jobs",
    )
    matches: Mapped[list["JobMatch"]] = relationship(
        "JobMatch",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["JobReport"]] = relationship(
        "JobReport",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    cover_letter_logs: Mapped[list["CoverLetterLog"]] = relationship(
        "CoverLetterLog",
        back_populates="job",
        cascade="all, delete-orphan",
    )

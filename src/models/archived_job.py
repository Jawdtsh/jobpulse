import uuid
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from src.models.base import UUIDPrimaryKeyMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.monitored_channel import MonitoredChannel


class ArchivedJob(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "archived_jobs"

    original_job_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    source_channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitored_channels.id", ondelete="SET NULL"),
        nullable=True,
    )
    telegram_message_id: Mapped[int] = mapped_column(nullable=False)
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
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    archived_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    archive_reason: Mapped[str] = mapped_column(String(50), nullable=False)

    source_channel: Mapped["MonitoredChannel | None"] = relationship(
        "MonitoredChannel",
        back_populates="archived_jobs",
    )

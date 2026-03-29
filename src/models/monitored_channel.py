from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.job import Job
    from src.models.archived_job import ArchivedJob


class MonitoredChannel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "monitored_channels"

    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    member_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    jobs_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    false_positives: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_scraped_at: Mapped[datetime | None] = mapped_column(nullable=True)

    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="source_channel")
    archived_jobs: Mapped[list["ArchivedJob"]] = relationship(
        "ArchivedJob",
        back_populates="source_channel",
    )

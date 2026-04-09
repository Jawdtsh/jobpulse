import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, LargeBinary, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from pgvector.sqlalchemy import Vector
from src.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class UserCV(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_cvs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    embedding_vector: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    experience_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    completeness_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    improvement_suggestions: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="cvs")

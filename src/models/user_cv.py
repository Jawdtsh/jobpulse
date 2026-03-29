import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
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

    user: Mapped["User"] = relationship("User", back_populates="cvs")

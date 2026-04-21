import uuid

from sqlalchemy import BigInteger, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import UUIDPrimaryKeyMixin
from src.database import Base


class AdminActionLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "admin_action_log"

    admin_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    amount_usd = mapped_column(Numeric(10, 2), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

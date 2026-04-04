from datetime import datetime
from sqlalchemy import Boolean, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from src.database import Base


class TelegramSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "telegram_sessions"

    session_string: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

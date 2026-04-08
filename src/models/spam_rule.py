from sqlalchemy import Boolean, CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from src.database import Base


class SpamRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "spam_rules"
    __table_args__ = (
        CheckConstraint(
            "rule_type IN ('spam_keyword', 'scam_indicator')",
            name="ck_spam_rules_rule_type",
        ),
        UniqueConstraint("pattern", "rule_type", name="uq_spam_rules_pattern_type"),
    )

    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

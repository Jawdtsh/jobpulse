import uuid
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from src.database import Base

if TYPE_CHECKING:
    from src.models.user_cv import UserCV
    from src.models.job_match import JobMatch
    from src.models.subscription import Subscription
    from src.models.referral_reward import ReferralReward
    from src.models.cover_letter_log import CoverLetterLog
    from src.models.user_interaction import UserInteraction
    from src.models.job_report import JobReport
    from src.models.language import Language


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referral_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    subscription_tier: Mapped[str] = mapped_column(
        String(20), default="free", nullable=False
    )
    referred_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    language_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("languages.id"),
        default=1,
        nullable=False,
    )

    cvs: Mapped[list["UserCV"]] = relationship(
        "UserCV",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    job_matches: Mapped[list["JobMatch"]] = relationship(
        "JobMatch",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    referral_rewards_as_referrer: Mapped[list["ReferralReward"]] = relationship(
        "ReferralReward",
        foreign_keys="ReferralReward.referrer_id",
        back_populates="referrer",
    )
    referral_rewards_as_referred: Mapped[list["ReferralReward"]] = relationship(
        "ReferralReward",
        foreign_keys="ReferralReward.referred_user_id",
        back_populates="referred_user",
    )
    cover_letter_logs: Mapped[list["CoverLetterLog"]] = relationship(
        "CoverLetterLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    interactions: Mapped[list["UserInteraction"]] = relationship(
        "UserInteraction",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    language: Mapped["Language"] = relationship("Language")
    job_reports: Mapped[list["JobReport"]] = relationship(
        "JobReport",
        back_populates="reporter_user",
        cascade="all, delete-orphan",
    )

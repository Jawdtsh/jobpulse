from src.database import Base, get_async_session
from src.models import (
    User,
    UserCV,
    Job,
    JobMatch,
    Subscription,
    ReferralReward,
    CoverLetterLog,
    UserInteraction,
    JobReport,
    ArchivedJob,
    TelegramSession,
    MonitoredChannel,
)
from src.repositories import (
    AbstractRepository,
    UserRepository,
    CVRepository,
    JobRepository,
    MatchRepository,
    SubscriptionRepository,
    ReferralRewardRepository,
    CoverLetterRepository,
    InteractionRepository,
    ReportRepository,
    ArchivedJobRepository,
    TelegramSessionRepository,
    ChannelRepository,
)


def __getattr__(name) -> object:
    if name in ("engine", "async_session_maker"):
        from src.database import _ensure_engine

        _ensure_engine()
        from src import database

        if name == "engine":
            return database._engine
        return database._async_session_maker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Base",
    "engine",
    "async_session_maker",
    "get_async_session",
    "User",
    "UserCV",
    "Job",
    "JobMatch",
    "Subscription",
    "ReferralReward",
    "CoverLetterLog",
    "UserInteraction",
    "JobReport",
    "ArchivedJob",
    "TelegramSession",
    "MonitoredChannel",
    "AbstractRepository",
    "UserRepository",
    "CVRepository",
    "JobRepository",
    "MatchRepository",
    "SubscriptionRepository",
    "ReferralRewardRepository",
    "CoverLetterRepository",
    "InteractionRepository",
    "ReportRepository",
    "ArchivedJobRepository",
    "TelegramSessionRepository",
    "ChannelRepository",
]

from src.repositories.base import AbstractRepository
from src.repositories.user_repository import UserRepository
from src.repositories.cv_repository import CVRepository
from src.repositories.job_repository import JobRepository
from src.repositories.match_repository import MatchRepository
from src.repositories.subscription_repository import SubscriptionRepository
from src.repositories.referral_reward_repository import ReferralRewardRepository
from src.repositories.cover_letter_repository import CoverLetterRepository
from src.repositories.interaction_repository import InteractionRepository
from src.repositories.report_repository import ReportRepository
from src.repositories.archived_job_repository import ArchivedJobRepository
from src.repositories.telegram_session_repository import TelegramSessionRepository
from src.repositories.channel_repository import ChannelRepository

__all__ = [
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

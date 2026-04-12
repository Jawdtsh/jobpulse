import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_preferences import UserPreferences
from src.models.job_category import JobCategory
from src.services.exceptions import ThresholdOutOfRangeError
from config.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 0.80
MIN_USER_THRESHOLD = 0.60
MAX_USER_THRESHOLD = 1.00


class ThresholdService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_effective_threshold(
        self, user_id: uuid.UUID, category_name: str | None = None
    ) -> float:
        user_threshold = await self._get_user_threshold(user_id)
        if user_threshold is not None:
            return user_threshold

        if category_name:
            category_threshold = await self._get_category_threshold(category_name)
            if category_threshold is not None:
                return category_threshold

        settings = get_settings()
        return settings.matching.matching_threshold_default

    async def set_user_threshold(
        self, user_id: uuid.UUID, threshold: float
    ) -> UserPreferences:
        if not MIN_USER_THRESHOLD <= threshold <= MAX_USER_THRESHOLD:
            raise ThresholdOutOfRangeError(value=threshold)

        stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
        result = await self._session.execute(stmt)
        prefs = result.scalar_one_or_none()

        if prefs:
            prefs.similarity_threshold = threshold
            await self._session.flush()
            return prefs

        prefs = UserPreferences(user_id=user_id, similarity_threshold=threshold)
        self._session.add(prefs)
        await self._session.flush()
        return prefs

    async def _get_user_threshold(self, user_id: uuid.UUID) -> float | None:
        stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
        result = await self._session.execute(stmt)
        prefs = result.scalar_one_or_none()
        if prefs and prefs.similarity_threshold is not None:
            return prefs.similarity_threshold
        return None

    async def _get_category_threshold(self, category_name: str) -> float | None:
        stmt = select(JobCategory).where(JobCategory.name == category_name)
        result = await self._session.execute(stmt)
        category = result.scalar_one_or_none()
        if category:
            return category.similarity_threshold
        return None

    async def set_category_threshold(
        self, category_name: str, threshold: float
    ) -> JobCategory:
        if not 0.00 <= threshold <= 1.00:
            raise ThresholdOutOfRangeError(value=threshold)

        stmt = select(JobCategory).where(JobCategory.name == category_name)
        result = await self._session.execute(stmt)
        category = result.scalar_one_or_none()

        if category:
            category.similarity_threshold = threshold
        else:
            category = JobCategory(name=category_name, similarity_threshold=threshold)
            self._session.add(category)

        await self._session.flush()
        return category

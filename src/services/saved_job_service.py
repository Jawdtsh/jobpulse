import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.saved_job import SavedJob
from src.repositories.saved_job_repository import SavedJobRepository

logger = logging.getLogger(__name__)


class SavedJobService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SavedJobRepository(session)

    async def save(self, user_id: uuid.UUID, job_id: uuid.UUID) -> SavedJob:
        existing = await self._repo.get_by_user_and_job(user_id, job_id)
        if existing:
            return existing
        saved = await self._repo.save_job(user_id, job_id)
        logger.info("Job saved user=%s job=%s", user_id, job_id)
        return saved

    async def unsave(self, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        result = await self._repo.unsave_job(user_id, job_id)
        if result:
            logger.info("Job unsaved user=%s job=%s", user_id, job_id)
        return result

    async def is_saved(self, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        return await self._repo.get_by_user_and_job(user_id, job_id) is not None

    async def get_saved_jobs(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 5,
    ) -> list[SavedJob]:
        return await self._repo.get_saved_by_user(user_id, skip=skip, limit=limit)

    async def count_saved(self, user_id: uuid.UUID) -> int:
        return await self._repo.count_saved_by_user(user_id)

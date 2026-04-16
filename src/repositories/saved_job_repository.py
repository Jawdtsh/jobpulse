import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.saved_job import SavedJob
from src.repositories.base import AbstractRepository


class SavedJobRepository(AbstractRepository[SavedJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SavedJob)

    async def get_by_user_and_job(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> Optional[SavedJob]:
        stmt = select(SavedJob).where(
            SavedJob.user_id == user_id,
            SavedJob.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_saved_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 5,
        min_similarity: float | None = None,
        days: int | None = None,
    ) -> list[SavedJob]:
        stmt = (
            select(SavedJob)
            .where(SavedJob.user_id == user_id)
            .order_by(SavedJob.saved_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_saved_by_user(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(SavedJob)
            .where(SavedJob.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def save_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> SavedJob:
        return await self.create(
            user_id=user_id,
            job_id=job_id,
            saved_at=datetime.now(timezone.utc),
        )

    async def unsave_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        saved = await self.get_by_user_and_job(user_id, job_id)
        if saved is None:
            return False
        await self.delete(saved.id)
        return True

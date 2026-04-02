import uuid
from typing import Optional, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.archived_job import ArchivedJob
from src.repositories.base import AbstractRepository


class ArchivedJobRepository(AbstractRepository[ArchivedJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ArchivedJob)

    async def get_by_original_job_id(
        self, original_job_id: uuid.UUID
    ) -> Optional[ArchivedJob]:
        stmt = select(ArchivedJob).where(ArchivedJob.original_job_id == original_job_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_archived_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ArchivedJob]:
        stmt = (
            select(ArchivedJob)
            .order_by(ArchivedJob.archived_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_channel(
        self,
        channel_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ArchivedJob]:
        stmt = (
            select(ArchivedJob)
            .where(
                ArchivedJob.source_channel_id == channel_id,
            )
            .order_by(ArchivedJob.archived_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_archived_job(
        self,
        original_job_id: uuid.UUID,
        title: str,
        company: str,
        description: str,
        content_hash: str,
        archive_reason: str,
        telegram_message_id: int,
        source_channel_id: Optional[uuid.UUID] = None,
        location: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        salary_currency: str = "USD",
        requirements: Optional[list[Any]] = None,
        skills: Optional[list[str]] = None,
    ) -> ArchivedJob:
        return await self.create(
            original_job_id=original_job_id,
            title=title,
            company=company,
            description=description,
            content_hash=content_hash,
            archive_reason=archive_reason,
            telegram_message_id=telegram_message_id,
            source_channel_id=source_channel_id,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            requirements=requirements or [],
            skills=skills or [],
        )

    async def count_by_reason(self, archive_reason: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ArchivedJob)
            .where(ArchivedJob.archive_reason == archive_reason)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

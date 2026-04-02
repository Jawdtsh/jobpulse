import uuid
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.job_report import JobReport
from src.repositories.base import AbstractRepository


class ReportRepository(AbstractRepository[JobReport]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, JobReport)

    async def get_reports_by_job(
        self,
        job_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobReport]:
        stmt = (
            select(JobReport)
            .where(
                JobReport.job_id == job_id,
            )
            .order_by(JobReport.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_unique_reporters_for_job(self, job_id: uuid.UUID) -> int:
        stmt = select(func.count(JobReport.reporter_user_id.distinct())).where(
            JobReport.job_id == job_id
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def has_user_reported_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        stmt = select(JobReport).where(
            JobReport.job_id == job_id,
            JobReport.reporter_user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_report(
        self,
        job_id: uuid.UUID,
        reporter_user_id: uuid.UUID,
        reason: str,
        details: Optional[str] = None,
    ) -> Optional[JobReport]:
        if await self.has_user_reported_job(job_id, reporter_user_id):
            return None
        return await self.create(
            job_id=job_id,
            reporter_user_id=reporter_user_id,
            reason=reason,
            details=details,
        )

    async def should_auto_archive(self, job_id: uuid.UUID, threshold: int = 3) -> bool:
        count = await self.count_unique_reporters_for_job(job_id)
        return count >= threshold

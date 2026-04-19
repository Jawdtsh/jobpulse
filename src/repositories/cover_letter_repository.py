import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.cover_letter_log import CoverLetterLog
from src.repositories.base import AbstractRepository


class CoverLetterRepository(AbstractRepository[CoverLetterLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CoverLetterLog)

    async def get_monthly_count(self, user_id: uuid.UUID) -> int:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count(CoverLetterLog.id)).where(
            and_(
                CoverLetterLog.user_id == user_id,
                CoverLetterLog.generated_at >= month_start,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_logs_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CoverLetterLog]:
        stmt = (
            select(CoverLetterLog)
            .where(
                CoverLetterLog.user_id == user_id,
            )
            .order_by(CoverLetterLog.generated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_log(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        cv_id: uuid.UUID | None = None,
        content: str = "",
        tone: str = "professional",
        length: str = "medium",
        focus_area: str = "all",
        language: str = "english",
        ai_model: str = "",
        generation_count: int = 1,
        counted_in_quota: bool = True,
    ) -> CoverLetterLog:
        return await self.create(
            user_id=user_id,
            job_id=job_id,
            cv_id=cv_id,
            content=content,
            tone=tone,
            length=length,
            focus_area=focus_area,
            language=language,
            ai_model=ai_model,
            generation_count=generation_count,
            generated_at=datetime.now(timezone.utc),
            counted_in_quota=counted_in_quota,
        )

    async def check_quota_available(
        self,
        user_id: uuid.UUID,
        monthly_limit: int,
    ) -> bool:
        logs = await self.get_logs_for_update(user_id)
        return len(logs) < monthly_limit

    async def get_logs_for_update(
        self,
        user_id: uuid.UUID,
        month: Optional[datetime] = None,
    ) -> list[CoverLetterLog]:
        if month is None:
            month = datetime.now(timezone.utc)
        month_start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(CoverLetterLog)
            .where(
                and_(
                    CoverLetterLog.user_id == user_id,
                    CoverLetterLog.generated_at >= month_start,
                )
            )
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_for_job(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> Optional[CoverLetterLog]:
        stmt = (
            select(CoverLetterLog)
            .where(
                and_(
                    CoverLetterLog.user_id == user_id,
                    CoverLetterLog.job_id == job_id,
                )
            )
            .order_by(CoverLetterLog.generated_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, cover_letter_id: uuid.UUID) -> Optional[CoverLetterLog]:
        return await self.get(cover_letter_id)

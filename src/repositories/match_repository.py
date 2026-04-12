import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.job_match import JobMatch
from src.repositories.base import AbstractRepository


class MatchRepository(AbstractRepository[JobMatch]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, JobMatch)

    async def get_by_job_and_user(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[JobMatch]:
        stmt = select(JobMatch).where(
            JobMatch.job_id == job_id,
            JobMatch.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_existing_match_keys(
        self,
        user_id: uuid.UUID,
        job_ids: list[uuid.UUID],
        cv_ids: list[uuid.UUID],
    ) -> set[tuple[uuid.UUID, uuid.UUID, uuid.UUID]]:
        stmt = select(JobMatch.job_id, JobMatch.user_id, JobMatch.cv_id).where(
            JobMatch.user_id == user_id,
            JobMatch.job_id.in_(job_ids),
            JobMatch.cv_id.in_(cv_ids),
        )
        result = await self._session.execute(stmt)
        return {(row[0], row[1], row[2]) for row in result.all()}

    async def get_matches_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobMatch]:
        stmt = (
            select(JobMatch)
            .where(JobMatch.user_id == user_id)
            .order_by(JobMatch.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_unnotified_matches(self, user_id: uuid.UUID) -> list[JobMatch]:
        stmt = select(JobMatch).where(
            JobMatch.user_id == user_id,
            JobMatch.is_notified.is_(False),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_notified_matches_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[JobMatch]:
        stmt = (
            select(JobMatch)
            .where(
                JobMatch.user_id == user_id,
                JobMatch.is_notified.is_(True),
            )
            .order_by(JobMatch.notified_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_match(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        similarity_score: float,
        cv_id: uuid.UUID | None = None,
    ) -> Optional[JobMatch]:
        try:
            async with self._session.begin_nested():
                return await self.create(
                    job_id=job_id,
                    user_id=user_id,
                    similarity_score=similarity_score,
                    cv_id=cv_id,
                )
        except IntegrityError as e:
            if getattr(e.orig, "pgcode", None) == "23505":
                return None
            raise

    async def get_pending_by_cv(self, cv_id: uuid.UUID) -> list[JobMatch]:
        stmt = select(JobMatch).where(
            JobMatch.cv_id == cv_id,
            JobMatch.is_notified.is_(False),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_by_user(self, user_id: uuid.UUID) -> list[JobMatch]:
        stmt = select(JobMatch).where(
            JobMatch.user_id == user_id,
            JobMatch.is_notified.is_(False),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_ids(self, match_ids: list[uuid.UUID]) -> int:
        if not match_ids:
            return 0
        stmt = delete(JobMatch).where(JobMatch.id.in_(match_ids))
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount

    async def mark_notified(self, match_id: uuid.UUID) -> Optional[JobMatch]:
        return await self.update(
            match_id,
            is_notified=True,
            notified_at=datetime.now(timezone.utc),
        )

    async def mark_clicked(self, match_id: uuid.UUID) -> Optional[JobMatch]:
        return await self.update(
            match_id,
            is_clicked=True,
            clicked_at=datetime.now(timezone.utc),
        )

    async def count_clicked(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(JobMatch)
            .where(JobMatch.user_id == user_id, JobMatch.is_clicked.is_(True))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_notified(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(JobMatch)
            .where(JobMatch.user_id == user_id, JobMatch.is_notified.is_(True))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

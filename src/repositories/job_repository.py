import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, literal
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.job import Job
from src.repositories.base import AbstractRepository
from src.utils.vectors import generate_content_hash


class JobRepository(AbstractRepository[Job]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Job)

    async def get_by_content_hash(self, content_hash: str) -> Optional[Job]:
        stmt = select(Job).where(Job.content_hash == content_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_telegram_message(
        self,
        channel_id: uuid.UUID,
        message_id: int,
    ) -> Optional[Job]:
        stmt = select(Job).where(
            Job.source_channel_id == channel_id,
            Job.telegram_message_id == message_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_jobs(self, skip: int = 0, limit: int = 100) -> list[Job]:
        stmt = select(Job).where(~Job.is_archived).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_job(
        self,
        telegram_message_id: int,
        title: str,
        company: str,
        description: str,
        source_channel_id: Optional[uuid.UUID] = None,
        location: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        salary_currency: str = "USD",
        requirements: Optional[list] = None,
        skills: Optional[list[str]] = None,
        embedding_vector: Optional[list[float]] = None,
        content_hash: Optional[str] = None,
    ) -> Job:
        if content_hash is None:
            content_hash = generate_content_hash(f"{title}{company}{description}")
        return await self.create(
            telegram_message_id=telegram_message_id,
            title=title,
            company=company,
            description=description,
            source_channel_id=source_channel_id,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            requirements=requirements or [],
            skills=skills or [],
            embedding_vector=embedding_vector,
            content_hash=content_hash,
        )

    async def find_similar(
        self,
        embedding_vector: list[float],
        threshold: float = 0.8,
        limit: int = 10,
    ) -> list[tuple[Job, float]]:
        distance = Job.embedding_vector.cosine_distance(embedding_vector)
        similarity = literal(1.0) - distance
        stmt = (
            select(Job, similarity.label("similarity"))
            .where(
                ~Job.is_archived,
                Job.embedding_vector.isnot(None),
                similarity >= threshold,
            )
            .order_by(distance)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def archive_job(self, job_id: uuid.UUID) -> Optional[Job]:
        return await self.update(job_id, is_archived=True)

    async def get_jobs_since(self, since: datetime, limit: int = 500) -> list[Job]:
        stmt = (
            select(Job)
            .where(
                Job.created_at >= since,
                ~Job.is_archived,
                Job.embedding_vector.isnot(None),
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_embedding(
        self,
        job_id: uuid.UUID,
        embedding_vector: list[float],
    ) -> Optional[Job]:
        return await self.update(job_id, embedding_vector=embedding_vector)

    async def find_similar_to_cv(
        self,
        cv_embedding: list[float],
        threshold: float = 0.80,
        limit: int = 100,
        job_ids: list[uuid.UUID] | None = None,
    ) -> list[tuple[Job, float]]:
        distance = Job.embedding_vector.cosine_distance(cv_embedding)
        similarity = literal(1.0) - distance
        stmt = (
            select(Job, similarity.label("similarity"))
            .where(
                Job.embedding_vector.isnot(None),
                similarity >= threshold,
            )
            .order_by(similarity.desc())
            .limit(limit)
        )
        if job_ids is not None:
            stmt = stmt.where(Job.id.in_(job_ids))
        result = await self._session.execute(stmt)
        return [(row[0], float(row[1])) for row in result.all()]

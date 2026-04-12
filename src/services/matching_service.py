import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_cv import UserCV
from src.repositories.match_repository import MatchRepository
from src.repositories.cv_repository import CVRepository
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.services.exceptions import (
    JobNotFoundError,
    EmbeddingNotAvailableError,
    ProTierRequiredError,
)
from config.settings import get_settings

logger = logging.getLogger(__name__)

MATCHING_THRESHOLD_DEFAULT = 0.80
TIER_FREE = "free"
TIER_BASIC = "basic"
TIER_PRO = "pro"


class MatchingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._match_repo = MatchRepository(session)
        self._cv_repo = CVRepository(session)
        self._job_repo = JobRepository(session)
        self._user_repo = UserRepository(session)

    async def match_new_job(self, job_id: uuid.UUID) -> list[dict]:
        job = await self._job_repo.get(job_id)
        if not job:
            raise JobNotFoundError(job_id=str(job_id))
        if job.embedding_vector is None:
            logger.warning("Job %s has no embedding, skipping matching", job_id)
            raise EmbeddingNotAvailableError(entity_type="job", entity_id=str(job_id))

        active_cvs = await self._get_all_active_cvs()
        if not active_cvs:
            logger.info("No active CVs found for matching")
            return []

        results = []
        for cv in active_cvs:
            if cv.embedding_vector is None:
                logger.warning("CV %s has no embedding, skipping", cv.id)
                continue

            threshold = await self._get_threshold(cv.user_id)
            similarity = self._cosine_similarity(
                cv.embedding_vector, job.embedding_vector
            )

            if similarity >= threshold:
                match = await self._match_repo.create_match(
                    job_id=job.id,
                    user_id=cv.user_id,
                    similarity_score=round(similarity, 4),
                    cv_id=cv.id,
                )
                if match:
                    results.append(
                        {
                            "match_id": str(match.id),
                            "user_id": str(cv.user_id),
                            "cv_id": str(cv.id),
                            "similarity": round(similarity, 4),
                        }
                    )

        await self._session.flush()
        logger.info("Job %s matched against %d CVs", job_id, len(results))
        return results

    async def match_historical(
        self,
        user_id: uuid.UUID,
        days: int,
        resend_existing: bool = False,
    ) -> list[dict]:
        if not 1 <= days <= 7:
            raise ValueError("Days must be between 1 and 7")

        user = await self._user_repo.get(user_id)
        if not user or user.subscription_tier != TIER_PRO:
            raise ProTierRequiredError()

        since = datetime.now(timezone.utc) - timedelta(days=days)
        jobs = await self._job_repo.get_jobs_since(since)
        cvs = await self._cv_repo.get_active_cvs(user_id)

        if not cvs or not jobs:
            return []

        results = []
        for cv in cvs:
            if cv.embedding_vector is None:
                continue

            for job in jobs:
                if job.embedding_vector is None:
                    continue

                if not resend_existing:
                    existing = await self._match_repo.get_by_job_and_user(
                        job.id, user_id
                    )
                    if existing:
                        continue

                similarity = self._cosine_similarity(
                    cv.embedding_vector, job.embedding_vector
                )
                threshold = await self._get_threshold(user_id)

                if similarity >= threshold:
                    match = await self._match_repo.create_match(
                        job_id=job.id,
                        user_id=user_id,
                        similarity_score=round(similarity, 4),
                        cv_id=cv.id,
                    )
                    if match:
                        results.append(
                            {
                                "match_id": str(match.id),
                                "job_id": str(job.id),
                                "cv_id": str(cv.id),
                                "similarity": round(similarity, 4),
                            }
                        )

        await self._session.flush()
        logger.info("Historical match for user %s: %d results", user_id, len(results))
        return results

    async def _get_all_active_cvs(self) -> list[UserCV]:
        stmt = select(UserCV).where(
            UserCV.is_active.is_(True),
            UserCV.deleted_at.is_(None),
            UserCV.embedding_vector.isnot(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _get_threshold(self, user_id: uuid.UUID) -> float:
        settings = get_settings()
        try:
            from src.models.user_preferences import UserPreferences

            stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
            result = await self._session.execute(stmt)
            prefs = result.scalar_one_or_none()
            if prefs and prefs.similarity_threshold is not None:
                return prefs.similarity_threshold
        except Exception:
            pass
        return settings.matching.matching_threshold_default

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

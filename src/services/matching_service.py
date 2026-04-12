import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.match_repository import MatchRepository
from src.repositories.cv_repository import CVRepository
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.services.threshold_service import ThresholdService, DEFAULT_THRESHOLD
from src.services.exceptions import (
    JobNotFoundError,
    EmbeddingNotAvailableError,
    ProTierRequiredError,
)

logger = logging.getLogger(__name__)

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
        self._threshold_service = ThresholdService(session)

    async def match_new_job(self, job_id: uuid.UUID) -> list[dict]:
        job = await self._job_repo.get(job_id)
        if not job:
            raise JobNotFoundError(job_id=str(job_id))
        if job.embedding_vector is None:
            logger.warning("Job %s has no embedding, skipping matching", job_id)
            raise EmbeddingNotAvailableError(entity_type="job", entity_id=str(job_id))

        similar_cvs = await self._cv_repo.find_similar_cvs(
            job_embedding=job.embedding_vector,
            threshold=DEFAULT_THRESHOLD,
            limit=10000,
        )
        if not similar_cvs:
            logger.info("No similar CVs found for job %s", job_id)
            return []

        results = []
        for cv, score in similar_cvs:
            effective_threshold = await self._threshold_service.get_effective_threshold(
                cv.user_id
            )
            if score < effective_threshold:
                continue

            match = await self._match_repo.create_match(
                job_id=job.id,
                user_id=cv.user_id,
                similarity_score=round(score, 4),
                cv_id=cv.id,
            )
            if match:
                results.append(
                    {
                        "match_id": str(match.id),
                        "user_id": str(cv.user_id),
                        "cv_id": str(cv.id),
                        "similarity": round(score, 4),
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

        if not jobs:
            return []

        effective_threshold = await self._threshold_service.get_effective_threshold(
            user_id
        )

        job_ids = [job.id for job in jobs if job.embedding_vector is not None]
        cvs = await self._cv_repo.get_active_cvs(user_id)
        if not cvs:
            return []
        cv_ids = [cv.id for cv in cvs]

        existing_keys = await self._match_repo.get_existing_match_keys(
            user_id, job_ids, cv_ids
        )

        results = []
        for job in jobs:
            if job.embedding_vector is None:
                continue

            similar_cvs = await self._cv_repo.find_similar_cvs(
                job_embedding=job.embedding_vector,
                threshold=effective_threshold,
                limit=10000,
            )

            for cv, score in similar_cvs:
                if cv.user_id != user_id:
                    continue

                if not resend_existing:
                    if (job.id, user_id, cv.id) in existing_keys:
                        continue

                match = await self._match_repo.create_match(
                    job_id=job.id,
                    user_id=user_id,
                    similarity_score=round(score, 4),
                    cv_id=cv.id,
                )
                if match:
                    results.append(
                        {
                            "match_id": str(match.id),
                            "job_id": str(job.id),
                            "cv_id": str(cv.id),
                            "similarity": round(score, 4),
                        }
                    )

        await self._session.flush()
        logger.info("Historical match for user %s: %d results", user_id, len(results))
        return results

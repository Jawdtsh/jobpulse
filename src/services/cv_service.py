import logging
import uuid
from io import BytesIO
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.cv_repository import CVRepository
from src.services.cv_evaluator import CVEvaluator, CVEvaluationResult
from src.services.cv_parser import CVParser
from src.services.exceptions import (
    CVDeletedError,
    CVFileSizeExceededError,
    CVFormatNotSupportedError,
    CVLimitExceededError,
    CVQuotaExceededError,
    CVTextExtractionError,
)

logger = logging.getLogger(__name__)

_MAX_FILE_SIZE = 5 * 1024 * 1024
_ALLOWED_FORMATS = {"pdf", "docx", "txt"}
_MIN_TEXT_LENGTH = 100

SUBSCRIPTION_CV_LIMITS = {
    "free": 1,
    "basic": 1,
    "pro": 2,
}

EVALUATION_QUOTAS = {
    "free": 1,
    "basic": 5,
    "pro": 10,
}


class CVService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CVRepository(session)
        self._parser = CVParser()
        self._evaluator = CVEvaluator()

    def validate_file(self, file_size: int, filename: str) -> str:
        if file_size > _MAX_FILE_SIZE:
            raise CVFileSizeExceededError(
                max_size_mb=5,
                file_size=file_size,
                filename=filename,
            )
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext not in _ALLOWED_FORMATS:
            raise CVFormatNotSupportedError(
                format=ext,
                filename=filename,
            )
        return ext

    async def upload_cv(
        self,
        user_id: uuid.UUID,
        file_data: BytesIO,
        filename: str,
        file_size: int,
    ) -> tuple[uuid.UUID, str, str]:
        fmt = self.validate_file(file_size, filename)

        cv_count = await self._repo.count_by_user(user_id)
        user_tier = await self._get_user_tier(user_id)
        limit = SUBSCRIPTION_CV_LIMITS.get(user_tier, 1)
        if cv_count >= limit:
            raise CVLimitExceededError(
                user_id=user_id,
                tier=user_tier,
                limit=limit,
                current_count=cv_count,
            )

        text = await self._parser.extract_text(file_data, fmt)
        if not text or len(text.strip()) < _MIN_TEXT_LENGTH:
            raise CVTextExtractionError(
                message=f"Extracted text too short ({len(text.strip())} chars, minimum {_MIN_TEXT_LENGTH})",
                user_id=user_id,
                filename=filename,
                text_length=len(text.strip()) if text else 0,
            )

        title = Path(filename).stem
        cv = await self._repo.create_cv(
            user_id=user_id,
            title=title,
            content=text,
            is_active=False,
        )
        logger.info(
            "CV uploaded user_id=%s cv_id=%s filename=%s",
            user_id,
            cv.id,
            filename,
            extra={
                "user_id": user_id,
                "cv_id": str(cv.id),
                "file_size": file_size,
                "file_format": fmt,
            },
        )
        return cv.id, title, text

    async def evaluate_cv(self, cv_id: uuid.UUID) -> CVEvaluationResult:
        cv = await self._repo.get(cv_id)
        if cv is None:
            raise CVDeletedError(cv_id=cv_id)
        if cv.deleted_at is not None:
            raise CVDeletedError(cv_id=cv_id)

        user_tier = await self._get_user_tier(cv.user_id)
        await self._check_evaluation_quota(cv.user_id, user_tier)

        text = self._repo.decrypt_content(cv)
        result = await self._evaluator.evaluate(text)

        await self._repo.update_evaluation(
            cv_id=cv_id,
            skills=result.skills,
            experience_summary=result.experience_summary,
            completeness_score=result.completeness_score,
            improvement_suggestions=result.improvement_suggestions,
        )

        if cv.is_active is False and result.completeness_score > 0:
            await self._repo.set_active_cv(cv_id, cv.user_id)

        from src.services.cv_quota_service import CVQuotaService

        quota_svc = CVQuotaService()
        await quota_svc.increment_usage(cv.user_id)

        logger.info(
            "CV evaluated cv_id=%s score=%s",
            cv_id,
            result.completeness_score,
            extra={
                "user_id": str(cv.user_id),
                "cv_id": str(cv_id),
                "completeness_score": str(result.completeness_score),
                "file_format": None,
                "file_size": None,
            },
        )
        return result

    async def _check_evaluation_quota(self, user_id: uuid.UUID, tier: str) -> None:
        from src.services.cv_quota_service import CVQuotaService

        quota_svc = CVQuotaService()
        allowed, remaining = await quota_svc.check_quota(user_id, tier)
        if not allowed:
            raise CVQuotaExceededError(
                user_id=user_id,
                tier=tier,
                remaining=remaining,
            )

    async def replace_cv(
        self,
        user_id: uuid.UUID,
        old_cv_id: uuid.UUID,
        file_data: BytesIO,
        filename: str,
        file_size: int,
    ) -> tuple[uuid.UUID, str, str]:
        old_cv = await self._repo.get(old_cv_id)
        if old_cv is None or old_cv.deleted_at is not None:
            raise CVDeletedError(cv_id=old_cv_id)

        await self._repo.soft_delete_cv(old_cv_id, user_id)

        return await self.upload_cv(
            user_id=user_id,
            file_data=file_data,
            filename=filename,
            file_size=file_size,
        )

    async def list_user_cvs(self, user_id: uuid.UUID) -> list:
        return await self._repo.get_by_user_id(user_id)

    async def activate_cv(self, cv_id: uuid.UUID, user_id: uuid.UUID):
        cv = await self._repo.get(cv_id)
        if cv is None or cv.deleted_at is not None:
            raise CVDeletedError(cv_id=cv_id)
        result = await self._repo.set_active_cv(cv_id, user_id)
        if result:
            from workers.celery_app import celery_app

            celery_app.send_task(
                "cv.match_active_cv_to_recent_jobs",
                args=[str(cv_id)],
            )
        return result

    async def deactivate_cv(self, cv_id: uuid.UUID, user_id: uuid.UUID):
        cv = await self._repo.get(cv_id)
        if cv is None or cv.deleted_at is not None:
            raise CVDeletedError(cv_id=cv_id)
        return await self._repo.deactivate_cv(cv_id, user_id)

    async def delete_cv(self, cv_id: uuid.UUID, user_id: uuid.UUID):
        cv = await self._repo.get(cv_id)
        if cv is None or cv.deleted_at is not None:
            raise CVDeletedError(cv_id=cv_id)
        return await self._repo.soft_delete_cv(cv_id, user_id)

    async def _get_user_tier(self, user_id: uuid.UUID) -> str:
        from src.repositories.user_repository import UserRepository

        user_repo = UserRepository(self._session)
        user = await user_repo.get(user_id)
        if user is None:
            return "free"
        return user.subscription_tier

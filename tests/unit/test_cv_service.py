import uuid
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.cv_service import CVService
from src.services.exceptions import (
    CVDeletedError,
    CVFileSizeExceededError,
    CVFormatNotSupportedError,
    CVLimitExceededError,
    CVQuotaExceededError,
    CVTextExtractionError,
    CVUploadInProgressError,
)


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.set.return_value = True
    return redis


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_repo, mock_redis):
    with (
        patch("src.services.cv_service.CVRepository", return_value=mock_repo),
        patch("src.services.cv_service.CVParser") as MockParser,
        patch("src.services.cv_service.CVEvaluator"),
    ):
        mock_parser = MockParser.return_value
        mock_parser.extract_text = AsyncMock(return_value="A" * 200)
        svc = CVService(mock_session)
        svc._redis = mock_redis
        return svc


class TestCVServiceValidation:
    def test_validate_file_success(self, service):
        ext = service.validate_file(1024, "resume.pdf")
        assert ext == "pdf"

    def test_validate_file_rejects_large_file(self, service):
        with pytest.raises(CVFileSizeExceededError):
            service.validate_file(10 * 1024 * 1024, "big.pdf")

    def test_validate_file_rejects_unsupported_format(self, service):
        with pytest.raises(CVFormatNotSupportedError):
            service.validate_file(1024, "resume.xlsx")

    def test_validate_file_accepts_docx(self, service):
        assert service.validate_file(1024, "cv.docx") == "docx"

    def test_validate_file_accepts_txt(self, service):
        assert service.validate_file(1024, "cv.txt") == "txt"


class TestCVServiceUpload:
    @pytest.mark.asyncio
    async def test_upload_cv_success(self, service, mock_repo, mock_redis):
        mock_cv = MagicMock()
        mock_cv.id = uuid.uuid4()
        mock_repo.count_active_by_user.return_value = 0
        mock_repo.create_cv.return_value = mock_cv

        with patch.object(service, "_get_user_tier", return_value="free"):
            cv_id, title, _text = await service.upload_cv(
                user_id=uuid.uuid4(),
                file_data=BytesIO(b"data"),
                filename="test.pdf",
                file_size=1024,
            )

        assert cv_id == mock_cv.id
        assert title == "test"
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_cv_limit_exceeded(self, service, mock_repo, mock_redis):
        mock_repo.count_active_by_user.return_value = 1
        user_id = uuid.uuid4()

        with patch.object(service, "_get_user_tier", return_value="free"):
            with pytest.raises(CVLimitExceededError):
                await service.upload_cv(
                    user_id=user_id,
                    file_data=BytesIO(b"data"),
                    filename="test.pdf",
                    file_size=1024,
                )

        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_cv_text_too_short(self, service, mock_repo, mock_redis):
        mock_repo.count_active_by_user.return_value = 0
        service._parser.extract_text.return_value = "short"

        with patch.object(service, "_get_user_tier", return_value="free"):
            with pytest.raises(CVTextExtractionError):
                await service.upload_cv(
                    user_id=uuid.uuid4(),
                    file_data=BytesIO(b"data"),
                    filename="test.pdf",
                    file_size=1024,
                )

        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_cv_concurrent_rejected(self, service, mock_repo, mock_redis):
        mock_redis.set.return_value = False
        user_id = uuid.uuid4()

        with pytest.raises(CVUploadInProgressError):
            await service.upload_cv(
                user_id=user_id,
                file_data=BytesIO(b"data"),
                filename="test.pdf",
                file_size=1024,
            )

        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_cv_uses_active_count(self, service, mock_repo, mock_redis):
        mock_repo.count_active_by_user.return_value = 0
        mock_cv = MagicMock()
        mock_cv.id = uuid.uuid4()
        mock_repo.create_cv.return_value = mock_cv

        with patch.object(service, "_get_user_tier", return_value="free"):
            await service.upload_cv(
                user_id=uuid.uuid4(),
                file_data=BytesIO(b"data"),
                filename="test.pdf",
                file_size=1024,
            )

        mock_repo.count_active_by_user.assert_called_once()
        mock_repo.count_by_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_lock_key_format(self, service):
        user_id = uuid.UUID("12345678-1234-1234-1234-123456789abc")
        key = CVService._upload_lock_key(user_id)
        assert key == f"cv:upload:{user_id}"

    @pytest.mark.asyncio
    async def test_upload_lock_released_on_error(self, service, mock_repo, mock_redis):
        mock_repo.count_active_by_user.side_effect = RuntimeError("DB error")
        user_id = uuid.uuid4()

        with pytest.raises(RuntimeError):
            await service.upload_cv(
                user_id=user_id,
                file_data=BytesIO(b"data"),
                filename="test.pdf",
                file_size=1024,
            )

        mock_redis.delete.assert_called_once()


class TestCVServiceManage:
    @pytest.mark.asyncio
    async def test_delete_cv_success(self, service, mock_repo):
        cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_cv = MagicMock()
        mock_cv.deleted_at = None
        mock_repo.get.return_value = mock_cv
        mock_repo.soft_delete_cv.return_value = mock_cv

        result = await service.delete_cv(cv_id, user_id)
        assert result == mock_cv
        mock_repo.soft_delete_cv.assert_called_once_with(cv_id, user_id)

    @pytest.mark.asyncio
    async def test_delete_cv_already_deleted(self, service, mock_repo):
        cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_cv = MagicMock()
        mock_cv.deleted_at = "2026-01-01"
        mock_repo.get.return_value = mock_cv

        with pytest.raises(CVDeletedError):
            await service.delete_cv(cv_id, user_id)

    @pytest.mark.asyncio
    async def test_activate_cv_success(self, service, mock_repo):
        cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_cv = MagicMock()
        mock_cv.deleted_at = None
        mock_repo.get.return_value = mock_cv
        mock_repo.set_active_cv.return_value = mock_cv

        mock_celery = MagicMock()
        with patch.dict(
            "sys.modules", {"workers.celery_app": MagicMock(celery_app=mock_celery)}
        ):
            result = await service.activate_cv(cv_id, user_id)
            assert result == mock_cv
            mock_celery.send_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_cv_success(self, service, mock_repo):
        cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_cv = MagicMock()
        mock_cv.deleted_at = None
        mock_repo.get.return_value = mock_cv
        mock_repo.deactivate_cv.return_value = mock_cv

        result = await service.deactivate_cv(cv_id, user_id)
        assert result == mock_cv

    @pytest.mark.asyncio
    async def test_list_user_cvs(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_user_id.return_value = [MagicMock(), MagicMock()]

        result = await service.list_user_cvs(user_id)
        assert len(result) == 2
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_user_cvs_empty(self, service, mock_repo):
        user_id = uuid.uuid4()
        mock_repo.get_by_user_id.return_value = []

        result = await service.list_user_cvs(user_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_activate_cv_returns_none_on_failure(self, service, mock_repo):
        cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_cv = MagicMock()
        mock_cv.deleted_at = None
        mock_repo.get.return_value = mock_cv
        mock_repo.set_active_cv.return_value = None

        result = await service.activate_cv(cv_id, user_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_activate_cv_deleted_raises(self, service, mock_repo):
        cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_cv = MagicMock()
        mock_cv.deleted_at = "2026-01-01"
        mock_repo.get.return_value = mock_cv

        with pytest.raises(CVDeletedError):
            await service.activate_cv(cv_id, user_id)

    @pytest.mark.asyncio
    async def test_replace_cv_deactivates_old_and_creates_new(self, service, mock_repo):
        old_cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        new_cv_id = uuid.uuid4()

        old_cv = MagicMock()
        old_cv.deleted_at = None
        mock_repo.get.return_value = old_cv
        mock_repo.soft_delete_cv.return_value = old_cv

        new_cv = MagicMock()
        new_cv.id = new_cv_id
        mock_cv_created = MagicMock()
        mock_cv_created.id = new_cv_id
        mock_repo.create_cv.return_value = mock_cv_created
        mock_repo.count_active_by_user.return_value = 0

        with patch.object(service, "_get_user_tier", return_value="free"):
            result_id, title, text = await service.replace_cv(
                user_id=user_id,
                old_cv_id=old_cv_id,
                file_data=BytesIO(b"new content"),
                filename="new_cv.pdf",
                file_size=1024,
            )

        mock_repo.soft_delete_cv.assert_called_once_with(old_cv_id, user_id)
        mock_repo.create_cv.assert_called_once()
        assert result_id == new_cv_id


class TestCVServiceEvaluate:
    @pytest.mark.asyncio
    async def test_evaluate_cv_quota_exceeded(self, service, mock_repo):
        cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_cv = MagicMock()
        mock_cv.id = cv_id
        mock_cv.user_id = user_id
        mock_cv.deleted_at = None
        mock_repo.get.return_value = mock_cv

        mock_quota_svc = AsyncMock()
        mock_quota_svc.check_and_increment_quota.return_value = -1

        with patch.object(service, "_get_user_tier", return_value="free"):
            with patch(
                "src.services.cv_quota_service.CVQuotaService",
                return_value=mock_quota_svc,
            ):
                with pytest.raises(CVQuotaExceededError):
                    await service.evaluate_cv(cv_id)

    @pytest.mark.asyncio
    async def test_evaluate_cv_uses_atomic_quota(self, service, mock_repo):
        cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_cv = MagicMock()
        mock_cv.id = cv_id
        mock_cv.user_id = user_id
        mock_cv.deleted_at = None
        mock_cv.is_active = True
        mock_repo.get.return_value = mock_cv
        mock_repo.decrypt_content.return_value = "text"

        mock_result = MagicMock()
        mock_result.skills = ["Python"]
        mock_result.experience_summary = "5 years"
        mock_result.completeness_score = 80
        mock_result.improvement_suggestions = []
        service._evaluator.evaluate = AsyncMock(return_value=mock_result)

        mock_quota_svc = AsyncMock()
        mock_quota_svc.check_and_increment_quota.return_value = 1

        with patch.object(service, "_get_user_tier", return_value="free"):
            with patch(
                "src.services.cv_quota_service.CVQuotaService",
                return_value=mock_quota_svc,
            ):
                result = await service.evaluate_cv(cv_id)

        assert result == mock_result
        mock_quota_svc.check_and_increment_quota.assert_called_once_with(
            user_id, "free"
        )
        mock_repo.update_evaluation.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_cv_activates_with_zero_score(self, service, mock_repo):
        cv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_cv = MagicMock()
        mock_cv.id = cv_id
        mock_cv.user_id = user_id
        mock_cv.deleted_at = None
        mock_cv.is_active = False
        mock_repo.get.return_value = mock_cv
        mock_repo.decrypt_content.return_value = "text"

        mock_result = MagicMock()
        mock_result.skills = []
        mock_result.experience_summary = ""
        mock_result.completeness_score = 0
        mock_result.improvement_suggestions = []
        service._evaluator.evaluate = AsyncMock(return_value=mock_result)

        mock_quota_svc = AsyncMock()
        mock_quota_svc.check_and_increment_quota.return_value = 1

        with patch.object(service, "_get_user_tier", return_value="free"):
            with patch(
                "src.services.cv_quota_service.CVQuotaService",
                return_value=mock_quota_svc,
            ):
                result = await service.evaluate_cv(cv_id)

        assert result.completeness_score == 0
        mock_repo.set_active_cv.assert_called_once_with(cv_id, user_id)

    @pytest.mark.asyncio
    async def test_evaluate_cv_deleted_raises(self, service, mock_repo):
        cv_id = uuid.uuid4()
        mock_repo.get.return_value = None

        with pytest.raises(CVDeletedError):
            await service.evaluate_cv(cv_id)

import uuid
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.cv_service import CVService
from src.services.exceptions import (
    CVFileSizeExceededError,
    CVFormatNotSupportedError,
    CVLimitExceededError,
    CVTextExtractionError,
    CVDeletedError,
)


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_repo):
    with patch("src.services.cv_service.CVRepository", return_value=mock_repo):
        with patch("src.services.cv_service.CVParser"):
            with patch("src.services.cv_service.CVEvaluator"):
                svc = CVService(mock_session)
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
    async def test_upload_cv_success(self, service, mock_repo):
        mock_cv = MagicMock()
        mock_cv.id = uuid.uuid4()
        mock_repo.count_by_user.return_value = 0
        mock_repo.create_cv.return_value = mock_cv

        with patch.object(
            service._parser,
            "extract_text",
            return_value="A" * 200,
        ):
            cv_id, title, text = await service.upload_cv(
                user_id=uuid.uuid4(),
                file_data=BytesIO(b"data"),
                filename="test.pdf",
                file_size=1024,
            )

        assert cv_id == mock_cv.id
        assert title == "test"

    @pytest.mark.asyncio
    async def test_upload_cv_limit_exceeded(self, service, mock_repo):
        mock_repo.count_by_user.return_value = 1
        user_id = uuid.uuid4()

        with patch.object(service, "_get_user_tier", return_value="free"):
            with pytest.raises(CVLimitExceededError):
                await service.upload_cv(
                    user_id=user_id,
                    file_data=BytesIO(b"data"),
                    filename="test.pdf",
                    file_size=1024,
                )

    @pytest.mark.asyncio
    async def test_upload_cv_text_too_short(self, service, mock_repo):
        mock_repo.count_by_user.return_value = 0

        with patch.object(
            service._parser,
            "extract_text",
            return_value="short",
        ):
            with pytest.raises(CVTextExtractionError):
                await service.upload_cv(
                    user_id=uuid.uuid4(),
                    file_data=BytesIO(b"data"),
                    filename="test.pdf",
                    file_size=1024,
                )


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

        with patch("src.services.cv_service.celery_app") as mock_celery:
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

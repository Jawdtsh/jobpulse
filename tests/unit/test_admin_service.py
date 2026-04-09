import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.admin_service import AdminService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_session, mock_repo):
    with patch("src.services.admin_service.CVRepository", return_value=mock_repo):
        svc = AdminService(mock_session)
        return svc


def _make_settings():
    settings = MagicMock()
    settings.redis.redis_url = "redis://localhost:6379/0"
    return settings


def _make_mock_redis(mock_lock):
    mock_redis = MagicMock()
    mock_redis.lock.return_value = mock_lock
    mock_redis.from_url = MagicMock()
    mock_redis.aclose = AsyncMock()
    return mock_redis


def _make_cv(cv_id=None, content=b"gAAAAABf...encrypted"):
    cv = MagicMock()
    cv.id = cv_id or uuid.uuid4()
    cv.content = content
    return cv


class TestReencryptCvs:
    @pytest.mark.asyncio
    async def test_returns_failed_if_lock_not_acquired(self, service, mock_repo):
        mock_lock = AsyncMock()
        mock_lock.acquire.return_value = False

        with patch("config.settings.get_settings", return_value=_make_settings()):
            with patch(
                "redis.asyncio.from_url", return_value=_make_mock_redis(mock_lock)
            ):
                result = await service.reencrypt_cvs("old-key-base64")

        assert result["status"] == "failed"
        assert "already in progress" in result["error"]

    @pytest.mark.asyncio
    async def test_cursor_pagination_passes_last_id(self, service, mock_repo):
        cv1 = _make_cv(uuid.UUID("00000000-0000-0000-0000-000000000001"))
        cv2 = _make_cv(uuid.UUID("00000000-0000-0000-0000-000000000002"))
        mock_repo.get_all_for_reencryption.side_effect = [
            [cv1],
            [cv2],
            [],
        ]

        mock_lock = AsyncMock()
        mock_lock.acquire.return_value = True

        with patch("config.settings.get_settings", return_value=_make_settings()):
            with patch(
                "redis.asyncio.from_url", return_value=_make_mock_redis(mock_lock)
            ):
                with patch(
                    "src.services.admin_service.encrypt_data", return_value="enc"
                ):
                    with patch(
                        "cryptography.fernet.Fernet",
                        return_value=MagicMock(
                            decrypt=MagicMock(return_value=b"plaintext")
                        ),
                    ):
                        result = await service.reencrypt_cvs("old-key-base64")

        assert result["status"] == "success"
        assert result["total_reencrypted"] == 2

        calls = mock_repo.get_all_for_reencryption.call_args_list
        assert calls[0].kwargs["last_id"] is None
        assert calls[1].kwargs["last_id"] == cv1.id
        assert calls[2].kwargs["last_id"] == cv2.id

    @pytest.mark.asyncio
    async def test_handles_utf8_content(self, service, mock_repo):
        cv = _make_cv(content=b"encrypted-arabic-payload")
        mock_repo.get_all_for_reencryption.side_effect = [[cv], []]

        decrypted_text = "\u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645 - Hello World"
        mock_fernet = MagicMock()
        mock_fernet.decrypt.return_value = decrypted_text.encode("utf-8")

        mock_lock = AsyncMock()
        mock_lock.acquire.return_value = True

        with patch("config.settings.get_settings", return_value=_make_settings()):
            with patch(
                "redis.asyncio.from_url", return_value=_make_mock_redis(mock_lock)
            ):
                with patch(
                    "src.services.admin_service.encrypt_data", return_value="new-enc"
                ):
                    with patch("cryptography.fernet.Fernet", return_value=mock_fernet):
                        result = await service.reencrypt_cvs("old-key-base64")

        assert result["status"] == "success"
        assert result["total_reencrypted"] == 1
        mock_fernet.decrypt.assert_called_once_with(b"encrypted-arabic-payload")

    @pytest.mark.asyncio
    async def test_skips_failing_cv_and_continues(self, service, mock_repo):
        cv1 = _make_cv()
        cv2 = _make_cv()
        mock_repo.get_all_for_reencryption.side_effect = [[cv1, cv2], []]

        call_count = 0

        def mock_decrypt(data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Decryption failed")
            return b"plaintext"

        mock_fernet = MagicMock()
        mock_fernet.decrypt.side_effect = mock_decrypt

        mock_lock = AsyncMock()
        mock_lock.acquire.return_value = True

        with patch("config.settings.get_settings", return_value=_make_settings()):
            with patch(
                "redis.asyncio.from_url", return_value=_make_mock_redis(mock_lock)
            ):
                with patch(
                    "src.services.admin_service.encrypt_data", return_value="enc"
                ):
                    with patch("cryptography.fernet.Fernet", return_value=mock_fernet):
                        result = await service.reencrypt_cvs("old-key-base64")

        assert result["status"] == "success"
        assert result["total_reencrypted"] == 1

    @pytest.mark.asyncio
    async def test_lock_released_in_finally(self, service, mock_repo):
        mock_repo.get_all_for_reencryption.side_effect = RuntimeError("DB error")

        mock_lock = AsyncMock()
        mock_lock.acquire.return_value = True

        with patch("config.settings.get_settings", return_value=_make_settings()):
            with patch(
                "redis.asyncio.from_url", return_value=_make_mock_redis(mock_lock)
            ):
                with patch("cryptography.fernet.Fernet", return_value=MagicMock()):
                    result = await service.reencrypt_cvs("old-key-base64")

        assert result["status"] == "failed"
        mock_lock.release.assert_called_once()

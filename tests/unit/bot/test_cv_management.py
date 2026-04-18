from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.utils.i18n import t


def test_cv_management_uses_no_cvs_key():
    ar = t("no_cvs", "ar")
    en = t("no_cvs", "en")
    assert "سير" in ar
    assert "CV" in en or "upload" in en.lower()


def test_cv_list_header_key_exists():
    ar = t("cv_list_header", "ar")
    en = t("cv_list_header", "en")
    assert ar == "سيرتي الذاتية"
    assert en == "My CVs"


def test_subscribe_free_arabic_typo_fixed():
    ar = t("subscribe_free", "ar")
    assert "سيرات CV" not in ar
    assert "سير ذاتية" in ar


def test_subscribe_basic_arabic_typo_fixed():
    ar = t("subscribe_basic", "ar")
    assert "سيرات CV" not in ar
    assert "سير ذاتية" in ar


def test_subscribe_pro_arabic_typo_fixed():
    ar = t("subscribe_pro", "ar")
    assert "سيرات CV" not in ar
    assert "سير ذاتية" in ar


@pytest.mark.asyncio
async def test_my_cvs_uses_no_cvs_key():
    callback = MagicMock()
    callback.data = "cv_back"
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.from_user.language_code = "ar"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()

    message = MagicMock()
    message.text = "/my_cvs"
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.from_user.language_code = "ar"
    message.answer = AsyncMock()

    mock_session = AsyncMock()

    async def gen():
        yield mock_session

    user = MagicMock()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    cv_repo_instance = AsyncMock()
    cv_repo_instance.get_by_user_id = AsyncMock(return_value=[])

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
        patch(
            "src.repositories.cv_repository.CVRepository",
            return_value=cv_repo_instance,
        ),
    ):
        from src.bot.handlers.cv_management import cmd_my_cvs

        await cmd_my_cvs(message)

        text = message.answer.call_args[0][0]
        assert "سير" in text or "CV" in text
        assert "وظائف" not in text

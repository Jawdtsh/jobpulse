import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.handlers.settings import _render_settings, callback_toggle_notifications


def _make_callback(
    user_id: int = 123, lang_code: str = "ar", data: str = "toggle_notifications"
):
    callback = MagicMock()
    callback.from_user = MagicMock()
    callback.from_user.id = user_id
    callback.from_user.language_code = lang_code
    callback.data = data
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    return callback


def _make_message(user_id: int = 123, lang_code: str = "ar"):
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = user_id
    message.from_user.language_code = lang_code
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_toggle_notifications_no_prefs_creates_disabled():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.subscription_tier = "free"
    user.referral_code = "ABC12345"

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.execute = AsyncMock(
        return_value=AsyncMock(scalar_one_or_none=AsyncMock(return_value=None))
    )

    async def _mock_gen():
        yield mock_session

    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    with (
        patch("src.bot.handlers.settings.get_async_session", _mock_gen),
        patch("src.bot.handlers.settings.UserRepository", return_value=repo_instance),
        patch("src.bot.handlers.settings.ThresholdService") as mock_thresh,
    ):
        mock_thresh_instance = AsyncMock()
        mock_thresh_instance.get_effective_threshold = AsyncMock(return_value=0.8)
        mock_thresh.return_value = mock_thresh_instance

        callback = _make_callback()
        await callback_toggle_notifications(callback)

        callback.answer.assert_called_once()
        answer_text = callback.answer.call_args[0][0]
        assert "إيقاف" in answer_text or "disabled" in answer_text.lower()


@pytest.mark.asyncio
async def test_toggle_notifications_existing_prefs_toggles():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.subscription_tier = "free"
    user.referral_code = "ABC12345"

    prefs = MagicMock()
    prefs.notification_enabled = True

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.execute = AsyncMock(
        return_value=AsyncMock(scalar_one_or_none=AsyncMock(return_value=prefs))
    )

    async def _mock_gen():
        yield mock_session

    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    with (
        patch("src.bot.handlers.settings.get_async_session", _mock_gen),
        patch("src.bot.handlers.settings.UserRepository", return_value=repo_instance),
    ):
        callback = _make_callback()
        await callback_toggle_notifications(callback)

        assert prefs.notification_enabled is False


@pytest.mark.asyncio
async def test_render_settings_uses_message_answer_for_command():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.subscription_tier = "pro"
    user.referral_code = "XYZ99999"

    mock_session = AsyncMock()

    async def _mock_gen():
        yield mock_session

    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    mock_prefs_result = AsyncMock()
    mock_prefs_result.scalar_one_or_none = AsyncMock(return_value=None)

    mock_thresh_result = AsyncMock()
    mock_thresh_result.scalar_one_or_none = AsyncMock(return_value=None)

    mock_session.execute = AsyncMock(
        side_effect=[mock_thresh_result, mock_prefs_result]
    )

    with (
        patch("src.bot.handlers.settings.get_async_session", _mock_gen),
        patch("src.bot.handlers.settings.UserRepository", return_value=repo_instance),
        patch("src.bot.handlers.settings.ThresholdService") as mock_thresh,
    ):
        mock_thresh_instance = AsyncMock()
        mock_thresh_instance.get_effective_threshold = AsyncMock(return_value=0.8)
        mock_thresh.return_value = mock_thresh_instance

        message = _make_message()
        await _render_settings(message, message.from_user.id, "ar", edit=False)

        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "Pro" in text


@pytest.mark.asyncio
async def test_render_settings_uses_edit_text_for_callback():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.subscription_tier = "free"
    user.referral_code = "ABC12345"

    mock_session = AsyncMock()

    async def _mock_gen():
        yield mock_session

    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    mock_prefs_result = AsyncMock()
    mock_prefs_result.scalar_one_or_none = AsyncMock(return_value=None)

    mock_thresh_result = AsyncMock()
    mock_thresh_result.scalar_one_or_none = AsyncMock(return_value=None)

    mock_session.execute = AsyncMock(
        side_effect=[mock_thresh_result, mock_prefs_result]
    )

    with (
        patch("src.bot.handlers.settings.get_async_session", _mock_gen),
        patch("src.bot.handlers.settings.UserRepository", return_value=repo_instance),
        patch("src.bot.handlers.settings.ThresholdService") as mock_thresh,
    ):
        mock_thresh_instance = AsyncMock()
        mock_thresh_instance.get_effective_threshold = AsyncMock(return_value=0.8)
        mock_thresh.return_value = mock_thresh_instance

        callback = _make_callback()
        await _render_settings(callback, callback.from_user.id, "ar", edit=True)

        callback.message.edit_text.assert_called_once()

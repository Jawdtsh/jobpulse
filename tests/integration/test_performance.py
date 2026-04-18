import time
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.bot_session_service import BotSessionService


def _mock_session_gen():
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def gen():
        yield mock_session

    return gen, mock_session


@pytest.mark.asyncio
async def test_registration_response_time():
    start = time.monotonic()

    user = MagicMock()
    user.first_name = "Test"
    user.subscription_tier = "free"

    gen, mock_session = _mock_session_gen()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    message = MagicMock()
    message.text = "/start"
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.from_user.first_name = "Test"
    message.from_user.language_code = "ar"
    message.answer = AsyncMock()

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
    ):
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.memory import MemoryStorage

        state = FSMContext(storage=MemoryStorage(), key=MagicMock(user_id=123))

        from src.bot.handlers.registration import cmd_start

        await cmd_start(message, state)

    elapsed = time.monotonic() - start
    assert elapsed < 2.0, f"Registration took {elapsed:.2f}s, expected < 2s (SC-001)"


@pytest.mark.asyncio
async def test_session_expiry_within_threshold():
    svc = BotSessionService()
    mock_redis = AsyncMock()

    old_time = datetime(2026, 4, 16, 10, 0, 0, tzinfo=timezone.utc).isoformat()
    mock_redis.get = AsyncMock(
        return_value=f'{{"last_activity": "{old_time}", "current_state": "test", "flow_data": {{}}}}'
    )
    svc._redis = mock_redis

    assert await svc.is_expired(123) is True


@pytest.mark.asyncio
async def test_button_response_time():
    start = time.monotonic()

    job_id = uuid.uuid4()
    user_id = uuid.uuid4()

    callback = MagicMock()
    callback.data = f"save_job:{job_id}"
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.answer = AsyncMock()

    user = MagicMock()
    user.id = user_id

    gen, mock_session = _mock_session_gen()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    svc_instance = AsyncMock()
    svc_instance.is_saved = AsyncMock(return_value=False)
    svc_instance.save = AsyncMock()

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
        patch(
            "src.services.saved_job_service.SavedJobService", return_value=svc_instance
        ),
    ):
        from src.bot.handlers.job_notifications import callback_save_job

        await callback_save_job(callback)

    elapsed = time.monotonic() - start
    assert elapsed < 0.5, (
        f"Button response took {elapsed:.3f}s, expected < 500ms (SC-006)"
    )

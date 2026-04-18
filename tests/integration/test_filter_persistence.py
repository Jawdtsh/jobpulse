import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.handlers.saved_jobs import _relative_time


def test_relative_time_now():
    from datetime import datetime, timezone

    result = _relative_time(datetime.now(timezone.utc))
    assert "الآن" in result or "now" in result


def test_relative_time_minutes():
    from datetime import datetime, timezone, timedelta

    dt = datetime.now(timezone.utc) - timedelta(minutes=30)
    result = _relative_time(dt)
    assert "30" in result


def test_relative_time_hours():
    from datetime import datetime, timezone, timedelta

    dt = datetime.now(timezone.utc) - timedelta(hours=5)
    result = _relative_time(dt)
    assert "5" in result


def test_relative_time_days():
    from datetime import datetime, timezone, timedelta

    dt = datetime.now(timezone.utc) - timedelta(days=3)
    result = _relative_time(dt)
    assert "3" in result


def test_relative_time_none():
    result = _relative_time(None)
    assert result == ""


def _mock_session_gen():
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def gen():
        yield mock_session

    return gen, mock_session


@pytest.mark.asyncio
async def test_my_jobs_not_registered():
    gen, mock_session = _mock_session_gen()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=None)

    message = MagicMock()
    message.text = "/my_jobs"
    message.from_user = MagicMock()
    message.from_user.id = 999
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

        state = FSMContext(storage=MemoryStorage(), key=MagicMock(user_id=999))

        from src.bot.handlers.saved_jobs import cmd_my_jobs

        await cmd_my_jobs(message, state)

        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "/start" in text

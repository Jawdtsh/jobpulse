import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_session_gen():
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def gen():
        yield mock_session

    return gen, mock_session


@pytest.mark.asyncio
async def test_save_job_callback():
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

        svc_instance.save.assert_called_once_with(user_id, job_id)
        callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_save_job_already_saved():
    job_id = uuid.uuid4()

    callback = MagicMock()
    callback.data = f"save_job:{job_id}"
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.answer = AsyncMock()

    user = MagicMock()
    user.id = uuid.uuid4()

    gen, mock_session = _mock_session_gen()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    svc_instance = AsyncMock()
    svc_instance.is_saved = AsyncMock(return_value=True)

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

        svc_instance.save.assert_not_called()


@pytest.mark.asyncio
async def test_dismiss_match_callback():
    match_id = uuid.uuid4()

    callback = MagicMock()
    callback.data = f"dismiss_match:{match_id}"
    callback.from_user = MagicMock()
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.delete = AsyncMock()

    gen, mock_session = _mock_session_gen()
    match = MagicMock()
    match.id = match_id

    repo_instance = AsyncMock()
    repo_instance.get = AsyncMock(return_value=match)
    repo_instance.update = AsyncMock()

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.match_repository.MatchRepository",
            return_value=repo_instance,
        ),
    ):
        from src.bot.handlers.job_notifications import callback_dismiss_match

        await callback_dismiss_match(callback)

        repo_instance.update.assert_called_once_with(match_id, is_dismissed=True)
